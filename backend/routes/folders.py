from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from extensions import db
from models.material import Material, MaterialFolder


folders_bp = Blueprint("folders", __name__)


@folders_bp.get("")
@jwt_required()
def list_folders():
    user_id = int(get_jwt_identity())
    folders = (
        MaterialFolder.query.filter_by(user_id=user_id)
        .order_by(MaterialFolder.created_at.desc())
        .all()
    )
    return jsonify([folder.to_dict(include_count=True) for folder in folders])


@folders_bp.post("")
@jwt_required()
def create_folder():
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    description = (data.get("description") or "").strip()

    if not name:
        return jsonify({"message": "文件夹名称不能为空"}), 400
    if MaterialFolder.query.filter_by(user_id=user_id, name=name).first():
        return jsonify({"message": "文件夹名称已存在"}), 409

    folder = MaterialFolder(user_id=user_id, name=name, description=description)
    db.session.add(folder)
    db.session.commit()
    return jsonify(folder.to_dict(include_count=True)), 201


@folders_bp.put("/<int:folder_id>")
@jwt_required()
def update_folder(folder_id):
    user_id = int(get_jwt_identity())
    folder = MaterialFolder.query.filter_by(id=folder_id, user_id=user_id).first()
    if not folder:
        return jsonify({"message": "文件夹不存在"}), 404

    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    description = (data.get("description") or "").strip()
    if not name:
        return jsonify({"message": "文件夹名称不能为空"}), 400

    exists = (
        MaterialFolder.query.filter_by(user_id=user_id, name=name)
        .filter(MaterialFolder.id != folder_id)
        .first()
    )
    if exists:
        return jsonify({"message": "文件夹名称已存在"}), 409

    folder.name = name
    folder.description = description
    db.session.commit()
    return jsonify(folder.to_dict(include_count=True))


@folders_bp.delete("/<int:folder_id>")
@jwt_required()
def delete_folder(folder_id):
    user_id = int(get_jwt_identity())
    folder = MaterialFolder.query.filter_by(id=folder_id, user_id=user_id).first()
    if not folder:
        return jsonify({"message": "文件夹不存在"}), 404

    affected = Material.query.filter_by(user_id=user_id, folder_id=folder_id).all()
    for material in affected:
        material.folder_id = None
        material.sync_state = "sync_pending"
        if material.status == "ready":
            material.index_state = "stale"
    db.session.delete(folder)
    db.session.commit()
    return jsonify({"message": "删除成功，原文件夹内资料已移动到未分类"})
