from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from services.error_service import error_response
from services.stats_service import dashboard_stats, focus_duration_trend, folder_material_counts, material_types, task_trend


stats_bp = Blueprint("stats", __name__)


@stats_bp.get("/dashboard")
@jwt_required()
def dashboard():
    return jsonify(dashboard_stats(int(get_jwt_identity())))


@stats_bp.get("/task-trend")
@jwt_required()
def trend():
    return jsonify(task_trend(int(get_jwt_identity())))


@stats_bp.get("/material-types")
@jwt_required()
def types():
    return jsonify(material_types(int(get_jwt_identity())))


@stats_bp.get("/folders")
@jwt_required()
def folders():
    return jsonify(folder_material_counts(int(get_jwt_identity())))


@stats_bp.get("/focus-duration-trend")
@jwt_required()
def focus_trend():
    try:
        days = int(request.args.get("days", 7))
    except (TypeError, ValueError):
        return error_response("VALIDATION_ERROR", "days 必须是数字", status=400)
    if days < 1 or days > 30:
        return error_response("VALIDATION_ERROR", "days 必须在 1 到 30 之间", status=400)
    return jsonify(focus_duration_trend(int(get_jwt_identity()), days=days))
