from pathlib import Path
from uuid import uuid4

from flask import Blueprint, current_app, jsonify, request, send_file
from flask_jwt_extended import get_jwt_identity, jwt_required
from werkzeug.utils import secure_filename

from extensions import db
from models.material import Material, MaterialFolder, MaterialVisualAsset
from services.ai_service import AIService
from services.document_service import SUPPORTED_FILE_TYPES_LABEL, allowed_file, extract_text, split_text
from services.rag_service import RAGService
from services.visual_service import extract_visual_assets


materials_bp = Blueprint("materials", __name__)


@materials_bp.get("")
@jwt_required()
def list_materials():
    user_id = int(get_jwt_identity())
    folder_id = request.args.get("folder_id")

    query = Material.query.filter_by(user_id=user_id)
    if folder_id:
        query = query.filter_by(folder_id=int(folder_id))

    materials = query.order_by(Material.created_at.desc()).all()
    return jsonify([material.to_dict() for material in materials])


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
        return jsonify({"message": "图片资料不存在"}), 404
    image_path = Path(asset.image_path)
    if not image_path.exists():
        return jsonify({"message": "图片文件不存在"}), 404
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
    )
    db.session.add(material)
    db.session.commit()

    _process_material(material)
    return jsonify(material.to_dict()), 201


@materials_bp.post("/<int:material_id>/reindex")
@jwt_required()
def reindex_material(material_id):
    user_id = int(get_jwt_identity())
    material = Material.query.filter_by(id=material_id, user_id=user_id).first()
    if not material:
        return jsonify({"message": "资料不存在"}), 404
    _process_material(material, reindex=True)
    return jsonify(material.to_dict())


@materials_bp.delete("/<int:material_id>")
@jwt_required()
def delete_material(material_id):
    user_id = int(get_jwt_identity())
    material = Material.query.filter_by(id=material_id, user_id=user_id).first()
    if not material:
        return jsonify({"message": "资料不存在"}), 404

    RAGService().delete_material_indexes(material)
    file_path = Path(material.file_path)
    if file_path.exists():
        file_path.unlink()
    db.session.delete(material)
    db.session.commit()
    return jsonify({"message": "删除成功"})


def _process_material(material, reindex=False):
    try:
        text = extract_text(material.file_path)
        chunks = split_text(text)
        ai = AIService()
        material.summary = ai.summarize(text)
        material.keywords = ",".join(ai.extract_keywords(text))
        material.status = "ready" if chunks else "failed"
        rag = RAGService()
        if chunks:
            if reindex:
                rag.reindex_material(material, chunks)
            else:
                rag.index_material(material, chunks)

        try:
            if reindex:
                rag.delete_material_visual_vectors(material.user_id, material.id)
                MaterialVisualAsset.query.filter_by(material_id=material.id).delete()
                db.session.flush()
            visual_assets = extract_visual_assets(material)
            rag.index_visual_assets(material, visual_assets)
            visual_count = MaterialVisualAsset.query.filter_by(
                material_id=material.id,
            ).count()
            ready_visual_count = MaterialVisualAsset.query.filter_by(
                material_id=material.id,
                status="ready",
            ).count()
            if ready_visual_count:
                material.status = "ready"
            elif visual_count and not chunks:
                material.status = "failed"
                material.summary = (
                    f"{material.summary}\n\n视觉资料已提取，但未完成向量索引。请检查多模态 embedding 配置。"
                ).strip()
        except Exception as visual_exc:
            current_app.logger.warning("Visual assets were not indexed for material %s", material.id, exc_info=True)
            note = f"视觉索引未完成：{visual_exc}"
            material.summary = f"{material.summary}\n\n{note}".strip() if material.summary else note
        db.session.commit()
    except Exception as exc:
        current_app.logger.exception("Failed to process material %s", material.id)
        material.status = "failed"
        material.summary = f"资料处理失败：{exc}"
        db.session.commit()
