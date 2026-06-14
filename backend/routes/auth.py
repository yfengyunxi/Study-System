import os
from pathlib import Path
from uuid import uuid4

from flask import Blueprint, current_app, jsonify, request, send_file
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from werkzeug.utils import secure_filename

from extensions import db
from models.user import User


auth_bp = Blueprint("auth", __name__)

ALLOWED_AVATAR_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".avif"}


def _avatar_dir():
    path = Path(current_app.config["UPLOAD_FOLDER"]) / "avatars"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _clear_old_avatars(user_id):
    """Remove all old avatar files for this user."""
    avatar_dir = _avatar_dir()
    for f in avatar_dir.glob(f"{user_id}.*"):
        try:
            f.unlink()
        except OSError:
            pass


@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    nickname = (data.get("nickname") or username).strip()

    if not username or not password:
        return jsonify({"message": "用户名和密码不能为空"}), 400
    if len(password) < 6:
        return jsonify({"message": "密码至少需要 6 位"}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({"message": "用户名已存在"}), 409

    user = User(username=username, nickname=nickname)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    token = create_access_token(identity=str(user.id))
    return jsonify({"token": token, "user": user.to_dict()}), 201


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({"message": "用户名或密码错误"}), 401

    token = create_access_token(identity=str(user.id))
    return jsonify({"token": token, "user": user.to_dict()})


@auth_bp.get("/me")
@jwt_required()
def me():
    user = User.query.get(int(get_jwt_identity()))
    if not user:
        return jsonify({"message": "用户不存在"}), 404
    return jsonify(user.to_dict())


@auth_bp.put("/profile")
@jwt_required()
def update_profile():
    user = User.query.get(int(get_jwt_identity()))
    if not user:
        return jsonify({"message": "用户不存在"}), 404

    data = request.get_json(silent=True) or {}
    user.nickname = (data.get("nickname") or user.nickname).strip()
    # Only accept avatar URL string if no file upload is used (backward compat)
    if "avatar" in data and isinstance(data.get("avatar"), str):
        user.avatar = data["avatar"].strip() or user.avatar
    user.study_goal = (data.get("study_goal") or "").strip()
    db.session.commit()
    return jsonify(user.to_dict())


@auth_bp.post("/avatar")
@jwt_required()
def upload_avatar():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "用户不存在"}), 404

    file = request.files.get("file")
    if not file or not file.filename:
        return jsonify({"message": "请选择头像图片"}), 400

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_AVATAR_EXTS:
        return jsonify({"message": f"仅支持 {', '.join(ALLOWED_AVATAR_EXTS)} 格式"}), 400

    _clear_old_avatars(user_id)
    filename = f"{user_id}{ext}"
    filepath = _avatar_dir() / filename
    file.save(str(filepath))

    user.avatar = f"/api/auth/avatar/{user_id}?v={uuid4().hex[:8]}"
    db.session.commit()
    return jsonify(user.to_dict())


@auth_bp.get("/avatar/<int:user_id>")
def serve_avatar(user_id):
    avatar_dir = _avatar_dir()
    for ext in ALLOWED_AVATAR_EXTS:
        path = avatar_dir / f"{user_id}{ext}"
        if path.exists():
            return send_file(path)
    return jsonify({"message": "头像不存在"}), 404
