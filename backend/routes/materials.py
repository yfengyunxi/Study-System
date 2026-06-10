from pathlib import Path
from threading import Thread
from uuid import uuid4
from datetime import datetime

from flask import Blueprint, current_app, jsonify, request, send_file
from flask_jwt_extended import get_jwt_identity, jwt_required
from werkzeug.utils import secure_filename

from extensions import db
from models.material import Material, MaterialFolder, MaterialVisualAsset, ReindexJob
from services.ai_service import AIService
from services.document_service import SUPPORTED_FILE_TYPES_LABEL, allowed_file, extract_text, split_text
from services.error_service import error_response
from services.rag_service import RAGService
from services.visual_service import extract_visual_assets


materials_bp = Blueprint("materials", __name__)

VALID_MATERIAL_STATUSES = {"ready", "processing", "failed"}
VALID_MATERIAL_SORTS = {"created_desc", "title_asc", "status", "richness_desc"}
_ACTIVE_REINDEX_JOBS = set()


@materials_bp.get("")
@jwt_required()
def list_materials():
    user_id = int(get_jwt_identity())
    folder_id = request.args.get("folder_id")
    q = (request.args.get("q") or "").strip().lower()
    file_type = (request.args.get("file_type") or "").strip().lower()
    status = (request.args.get("status") or "").strip()
    sort = (request.args.get("sort") or "created_desc").strip() or "created_desc"

    if status and status not in VALID_MATERIAL_STATUSES:
        return jsonify({"message": "资料状态参数无效"}), 400
    try:
        has_visual_assets = _parse_bool_arg("has_visual_assets")
    except ValueError as exc:
        return jsonify({"message": str(exc)}), 400

    query = Material.query.filter_by(user_id=user_id)
    if folder_id:
        try:
            folder_id_int = int(folder_id)
        except ValueError:
            return jsonify({"message": "文件夹不存在"}), 404
        folder = MaterialFolder.query.filter_by(id=folder_id_int, user_id=user_id).first()
        if not folder:
            return jsonify({"message": "文件夹不存在"}), 404
        query = query.filter_by(folder_id=folder_id_int)
    if file_type:
        query = query.filter_by(file_type=file_type)
    if status:
        query = query.filter_by(status=status)

    materials = query.all()
    if q:
        materials = [
            material
            for material in materials
            if q in (material.title or "").lower()
            or q in (material.file_name or "").lower()
            or q in (material.folder.name if material.folder else "").lower()
            or q in (material.summary or "").lower()
            or q in (material.keywords or "").lower()
        ]
    if has_visual_assets is True:
        materials = [material for material in materials if len(material.visual_assets) > 0]
    if has_visual_assets is False:
        materials = [material for material in materials if len(material.visual_assets) == 0]

    warning = None
    if sort not in VALID_MATERIAL_SORTS:
        warning = "排序参数无效，已使用最新上传排序"
        sort = "created_desc"
    if sort == "created_desc":
        materials.sort(key=lambda item: item.created_at or item.id, reverse=True)
    elif sort == "title_asc":
        materials.sort(key=lambda item: item.title.lower())
    elif sort == "status":
        order = {"ready": 0, "processing": 1, "failed": 2}
        materials.sort(key=lambda item: (order.get(item.status, 99), item.title.lower()))
    elif sort == "richness_desc":
        materials.sort(key=lambda item: (_material_richness(item), item.created_at or item.id), reverse=True)

    response = jsonify([material.to_dict() for material in materials])
    if warning:
        response.headers["X-StudyHub-Warning"] = warning
    return response


@materials_bp.get("/<int:material_id>")
@jwt_required()
def get_material(material_id):
    user_id = int(get_jwt_identity())
    material = Material.query.filter_by(id=material_id, user_id=user_id).first()
    if not material:
        return jsonify({"message": "资料不存在"}), 404
    return jsonify(material.to_dict(include_chunks=True))


@materials_bp.get("/<int:material_id>/assets")
@jwt_required()
def list_material_assets(material_id):
    user_id = int(get_jwt_identity())
    material = Material.query.filter_by(id=material_id, user_id=user_id).first()
    if not material:
        return jsonify({"message": "资料不存在"}), 404
    assets = (
        MaterialVisualAsset.query.filter_by(user_id=user_id, material_id=material_id)
        .order_by(MaterialVisualAsset.asset_index)
        .all()
    )
    return jsonify([asset.to_dict() for asset in assets])


@materials_bp.get("/assets/<int:asset_id>/image")
@jwt_required()
def get_material_asset_image(asset_id):
    user_id = int(get_jwt_identity())
    asset = MaterialVisualAsset.query.filter_by(id=asset_id, user_id=user_id).first()
    if not asset:
        return error_response("IMAGE_ASSET_NOT_FOUND", "图片资料不存在", status=404)
    image_path = Path(asset.image_path)
    if not image_path.exists():
        asset.status = "missing_file"
        db.session.commit()
        return error_response("IMAGE_FILE_MISSING", "图片文件不存在", status=404, retryable=True)
    return send_file(image_path)


@materials_bp.post("/upload")
@jwt_required()
def upload_material():
    user_id = int(get_jwt_identity())
    file = request.files.get("file")
    title = (request.form.get("title") or "").strip()
    folder_id = request.form.get("folder_id")

    if not file:
        return jsonify({"message": "请选择要上传的文件"}), 400
    if not allowed_file(file.filename):
        return jsonify({"message": f"仅支持 {SUPPORTED_FILE_TYPES_LABEL}"}), 400

    folder_id = int(folder_id) if folder_id else None
    if folder_id and not MaterialFolder.query.filter_by(id=folder_id, user_id=user_id).first():
        return jsonify({"message": "文件夹不存在"}), 404

    original_name = file.filename or ""
    extension = Path(original_name).suffix.lower().lstrip(".")
    safe_original_name = secure_filename(original_name) or f"material.{extension}"
    stored_name = f"{uuid4().hex}.{extension}"
    upload_dir = Path(current_app.config["UPLOAD_FOLDER"]) / str(user_id)
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / stored_name
    file.save(file_path)

    material = Material(
        user_id=user_id,
        folder_id=folder_id,
        title=title or Path(original_name).stem or Path(safe_original_name).stem,
        file_name=original_name or safe_original_name,
        file_path=str(file_path),
        file_type=extension,
        status="processing",
        index_state="not_indexed",
        sync_state="synced",
        active_index_generation=0,
    )
    db.session.add(material)
    db.session.commit()

    _process_material(material)
    return jsonify(material.to_dict()), 201


@materials_bp.patch("/<int:material_id>/folder")
@jwt_required()
def move_material_folder(material_id):
    user_id = int(get_jwt_identity())
    material = Material.query.filter_by(id=material_id, user_id=user_id).first()
    if not material:
        return error_response("MATERIAL_NOT_FOUND", "资料不存在", status=404)
    if material.status == "deleted":
        return error_response("CONFLICT", "资料已删除，不能移动", status=409)

    data = request.get_json(silent=True) or {}
    try:
        target_folder_id = _parse_target_folder_id(data)
    except ValueError as exc:
        return error_response("VALIDATION_ERROR", str(exc), status=400)

    if target_folder_id is not None:
        folder = MaterialFolder.query.filter_by(id=target_folder_id, user_id=user_id).first()
        if not folder:
            return error_response("NOT_FOUND", "文件夹不存在", status=404)

    old_folder_id = material.folder_id
    if old_folder_id == target_folder_id:
        return jsonify(
            {
                "message": "资料已在目标文件夹",
                "changed": False,
                "sync_state": "synced",
                "material": material.to_dict(),
                "folder_counts": _folder_counts(user_id, {old_folder_id, target_folder_id}),
            }
        )

    material.folder_id = target_folder_id
    material.sync_state = "synced"
    MaterialVisualAsset.query.filter_by(user_id=user_id, material_id=material.id).update({"folder_id": target_folder_id})
    db.session.flush()

    try:
        RAGService().sync_material_folder_metadata(material)
        material.sync_state = "synced"
        if material.status == "ready" and material.index_state == "stale":
            material.index_state = "ready"
        db.session.commit()
        return jsonify(
            {
                "message": "资料已移动到文件夹" if target_folder_id else "资料已移回未分类",
                "changed": True,
                "sync_state": "synced",
                "material": material.to_dict(),
                "folder_counts": _folder_counts(user_id, {old_folder_id, target_folder_id}),
            }
        )
    except Exception:
        current_app.logger.warning("Vector metadata sync failed after material move", exc_info=True)
        material.sync_state = "sync_failed"
        material.index_state = "stale"
        db.session.commit()
        return jsonify(
            {
                "message": "资料已移动，但索引同步失败，可重建索引修复检索范围",
                "changed": True,
                "sync_state": "sync_failed",
                "error_code": "VECTOR_SYNC_FAILED",
                "retryable": True,
                "material": material.to_dict(),
                "folder_counts": _folder_counts(user_id, {old_folder_id, target_folder_id}),
            }
        )


@materials_bp.post("/<int:material_id>/reindex")
@jwt_required()
def reindex_material(material_id):
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}
    material = Material.query.filter_by(id=material_id, user_id=user_id).first()
    if not material:
        return error_response("MATERIAL_NOT_FOUND", "资料不存在", status=404)

    active_job = (
        ReindexJob.query.filter(
            ReindexJob.user_id == user_id,
            ReindexJob.material_id == material_id,
            ReindexJob.status.in_(["queued", "running"]),
        )
        .order_by(ReindexJob.created_at.desc())
        .first()
    )
    if active_job:
        return jsonify({"message": "索引重建已在进行中", "job": active_job.to_dict(), "material": material.to_dict()}), 202

    next_generation = (material.active_index_generation or 0) + 1
    material.status = "processing"
    material.index_state = "queued"
    material.building_index_generation = next_generation
    job = ReindexJob(
        user_id=user_id,
        material_id=material.id,
        generation=next_generation,
        status="queued",
        phase="queued",
        request_id=(data.get("request_id") or "")[:120],
    )
    db.session.add(job)
    db.session.commit()

    _start_reindex_background(current_app._get_current_object(), job.id)
    return jsonify({"message": "索引重建已开始", "job": job.to_dict(), "material": material.to_dict()}), 202


@materials_bp.get("/<int:material_id>/index-status")
@jwt_required()
def material_index_status(material_id):
    user_id = int(get_jwt_identity())
    material = Material.query.filter_by(id=material_id, user_id=user_id).first()
    if not material:
        return error_response("MATERIAL_NOT_FOUND", "资料不存在", status=404)
    job = (
        ReindexJob.query.filter_by(user_id=user_id, material_id=material_id)
        .order_by(ReindexJob.created_at.desc())
        .first()
    )
    if job and job.status in {"queued", "running"} and job.id not in _ACTIVE_REINDEX_JOBS:
        _mark_reindex_job_stale(job, material)
        db.session.commit()
    ask_generation = material.active_index_generation or None
    return jsonify(
        {
            "material_id": material.id,
            "status": material.status,
            "index_state": material.index_state,
            "active_index_generation": material.active_index_generation,
            "building_index_generation": material.building_index_generation,
            "job": job.to_dict() if job else None,
            "ask_ai_available": bool(ask_generation),
            "ask_ai_uses_generation": ask_generation,
        }
    )


@materials_bp.delete("/<int:material_id>")
@jwt_required()
def delete_material(material_id):
    user_id = int(get_jwt_identity())
    material = Material.query.filter_by(id=material_id, user_id=user_id).first()
    if not material:
        return jsonify({"message": "资料不存在"}), 404

    for job in ReindexJob.query.filter(
        ReindexJob.user_id == user_id,
        ReindexJob.material_id == material_id,
        ReindexJob.status.in_(["queued", "running"]),
    ).all():
        job.status = "cancelled"
        job.phase = "cancelled"
        job.finished_at = datetime.utcnow()
    RAGService().delete_material_indexes(material)
    file_path = Path(material.file_path)
    if file_path.exists():
        file_path.unlink()
    db.session.delete(material)
    db.session.commit()
    return jsonify({"message": "删除成功"})


def _folder_counts(user_id, changed_folder_ids):
    counts = []
    folder_ids = [folder_id for folder_id in changed_folder_ids if folder_id is not None]
    for folder_id in folder_ids:
        counts.append(
            {
                "folder_id": folder_id,
                "material_count": Material.query.filter_by(user_id=user_id, folder_id=folder_id).count(),
            }
        )
    if None in changed_folder_ids:
        counts.append(
            {
                "folder_id": None,
                "material_count": Material.query.filter_by(user_id=user_id, folder_id=None).count(),
            }
        )
    return counts


def _parse_target_folder_id(data):
    if "folder_id" not in data or data.get("folder_id") is None:
        return None
    try:
        return int(data.get("folder_id"))
    except (TypeError, ValueError):
        raise ValueError("folder_id 必须是数字或 null")


def _parse_bool_arg(name):
    value = request.args.get(name)
    if value is None or value == "":
        return None
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    raise ValueError(f"{name} 必须为 true 或 false")


def _material_richness(material):
    keyword_count = len(material.to_dict().get("keywords", []))
    return len(material.chunks) + len(material.visual_assets) * 3 + min(keyword_count, 5)


def _start_reindex_background(app, job_id):
    if app.config.get("TESTING"):
        return
    _ACTIVE_REINDEX_JOBS.add(job_id)
    thread = Thread(target=_run_reindex_job, args=(app, job_id), daemon=True)
    thread.start()


def _mark_reindex_job_stale(job, material):
    job.status = "stale"
    job.phase = "stale_after_restart"
    job.retryable = True
    job.finished_at = datetime.utcnow()
    material.building_index_generation = None
    material.index_state = "stale" if material.active_index_generation else "failed"


def _run_reindex_job(app, job_id):
    with app.app_context():
        _ACTIVE_REINDEX_JOBS.add(job_id)
        try:
            job = db.session.get(ReindexJob, job_id)
            if not job or job.status != "queued":
                return
            material = Material.query.filter_by(id=job.material_id, user_id=job.user_id).first()
            if not material:
                job.status = "stale"
                job.retryable = True
                job.finished_at = datetime.utcnow()
                db.session.commit()
                return
            job.status = "running"
            job.phase = "extracting"
            job.started_at = datetime.utcnow()
            material.index_state = "running"
            db.session.commit()
            try:
                _process_material(material, reindex=True, generation=job.generation, job=job)
                material.active_index_generation = job.generation
                material.building_index_generation = None
                material.index_state = "ready"
                material.status = "ready"
                job.status = "succeeded"
                job.phase = "completed"
                job.retryable = False
            except Exception as exc:
                current_app.logger.warning("Reindex job failed for material %s", material.id, exc_info=True)
                material.building_index_generation = None
                material.index_state = "stale" if material.active_index_generation else "failed"
                material.status = "ready" if material.active_index_generation else "failed"
                job.status = "failed"
                job.phase = "failed"
                job.last_error = str(exc)
                job.error_code = "INDEX_FAILED"
                job.retryable = True
            finally:
                job.finished_at = datetime.utcnow()
                db.session.commit()
        finally:
            _ACTIVE_REINDEX_JOBS.discard(job_id)


def _process_material(material, reindex=False, generation=None, job=None):
    try:
        text = extract_text(material.file_path)
        chunks = split_text(text)
        ai = AIService()
        material.error_message = ""
        material.summary = ai.summarize(text)
        material.keywords = ",".join(ai.extract_keywords(text))
        material.status = "ready" if chunks else "failed"
        material.index_state = "ready" if chunks else "failed"
        if chunks and not material.active_index_generation:
            material.active_index_generation = generation or 1
        if not chunks:
            material.error_message = "未提取到可索引的文本内容"
        rag = RAGService()
        if chunks:
            if job:
                job.phase = "indexing_text"
                job.set_progress(chunks_indexed=len(chunks))
            if reindex:
                rag.reindex_material(material, chunks, generation=generation)
            else:
                rag.index_material(material, chunks, generation=generation or material.active_index_generation or 1)

        try:
            if reindex:
                rag.delete_material_visual_vectors(material.user_id, material.id)
                MaterialVisualAsset.query.filter_by(material_id=material.id).delete()
                db.session.flush()
            visual_assets = extract_visual_assets(material)
            rag.index_visual_assets(material, visual_assets, reindex=False, generation=generation or material.active_index_generation or 1)
            visual_count = MaterialVisualAsset.query.filter_by(
                material_id=material.id,
            ).count()
            ready_visual_count = MaterialVisualAsset.query.filter_by(
                material_id=material.id,
                status="ready",
            ).count()
            if job:
                job.phase = "indexing_visual"
                job.set_progress(
                    visual_assets_indexed=ready_visual_count,
                    visual_assets_failed=max(visual_count - ready_visual_count, 0),
                )
            if ready_visual_count:
                material.status = "ready"
                material.index_state = "ready"
                if chunks:
                    material.error_message = ""
            elif visual_count and not chunks:
                material.status = "failed"
                material.index_state = "failed"
                material.error_message = "视觉资产已提取，但未完成文本或视觉向量索引。请检查多模态 embedding 配置。"
        except Exception as visual_exc:
            current_app.logger.warning("Visual assets were not indexed for material %s", material.id, exc_info=True)
            if material.status != "ready":
                material.status = "failed"
                material.index_state = "failed"
            material.error_message = f"视觉索引未完成：{visual_exc}"
        db.session.commit()
    except Exception as exc:
        current_app.logger.exception("Failed to process material %s", material.id)
        material.status = "failed"
        material.index_state = "failed"
        material.summary = ""
        material.error_message = f"资料处理失败：{exc}"
        db.session.commit()
        if job:
            raise
