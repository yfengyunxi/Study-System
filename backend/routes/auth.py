from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required

from extensions import db
from models.user import User


auth_bp = Blueprint("auth", __name__)


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
    user.avatar = (data.get("avatar") or user.avatar).strip()
    user.study_goal = (data.get("study_goal") or "").strip()
    db.session.commit()
    return jsonify(user.to_dict())
