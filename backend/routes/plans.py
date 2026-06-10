from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from extensions import db
from models.plan import StudyPlan


plans_bp = Blueprint("plans", __name__)


@plans_bp.get("")
@jwt_required()
def list_plans():
    user_id = int(get_jwt_identity())
    plans = StudyPlan.query.filter_by(user_id=user_id).order_by(StudyPlan.created_at.desc()).all()
    return jsonify([plan.to_dict(include_tasks=True) for plan in plans])


@plans_bp.post("")
@jwt_required()
def create_plan():
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"message": "计划标题不能为空"}), 400

    try:
        start_date, end_date = _parse_plan_dates(data)
    except ValueError as exc:
        return jsonify({"message": str(exc)}), 400

    plan = StudyPlan(
        user_id=user_id,
        title=title,
        description=(data.get("description") or "").strip(),
        start_date=start_date,
        end_date=end_date,
    )
    db.session.add(plan)
    db.session.commit()
    return jsonify(plan.to_dict(include_tasks=True)), 201


@plans_bp.get("/<int:plan_id>")
@jwt_required()
def get_plan(plan_id):
    user_id = int(get_jwt_identity())
    plan = StudyPlan.query.filter_by(id=plan_id, user_id=user_id).first()
    if not plan:
        return jsonify({"message": "学习计划不存在"}), 404
    return jsonify(plan.to_dict(include_tasks=True))


@plans_bp.put("/<int:plan_id>")
@jwt_required()
def update_plan(plan_id):
    user_id = int(get_jwt_identity())
    plan = StudyPlan.query.filter_by(id=plan_id, user_id=user_id).first()
    if not plan:
        return jsonify({"message": "学习计划不存在"}), 404

    data = request.get_json(silent=True) or {}
    try:
        start_date, end_date = _parse_plan_dates(data)
    except ValueError as exc:
        return jsonify({"message": str(exc)}), 400
    plan.title = (data.get("title") or plan.title).strip()
    plan.description = (data.get("description") or "").strip()
    plan.start_date = start_date
    plan.end_date = end_date
    db.session.commit()
    return jsonify(plan.to_dict(include_tasks=True))


@plans_bp.delete("/<int:plan_id>")
@jwt_required()
def delete_plan(plan_id):
    user_id = int(get_jwt_identity())
    plan = StudyPlan.query.filter_by(id=plan_id, user_id=user_id).first()
    if not plan:
        return jsonify({"message": "学习计划不存在"}), 404
    db.session.delete(plan)
    db.session.commit()
    return jsonify({"message": "删除成功"})


def _parse_date_or_error(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError("日期格式必须为 YYYY-MM-DD")


def _parse_plan_dates(data):
    start_date = _parse_date_or_error(data.get("start_date"))
    end_date = _parse_date_or_error(data.get("end_date"))
    if start_date and end_date and end_date < start_date:
        raise ValueError("结束日期不能早于开始日期")
    return start_date, end_date


def _parse_date(value):
    return _parse_date_or_error(value)
