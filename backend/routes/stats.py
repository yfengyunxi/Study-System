from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required

from services.stats_service import dashboard_stats, folder_material_counts, material_types, task_trend


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
