from datetime import date, datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from extensions import db
from models.plan import StudyPlan, StudyTask


tasks_bp = Blueprint("tasks", __name__)


@tasks_bp.get("/today")
@jwt_required()
def today_tasks():
    user_id = int(get_jwt_identity())
    tasks = (
        StudyTask.query.filter_by(user_id=user_id, due_date=date.today())
        .order_by(StudyTask.created_at.desc())
        .all()
    )
    return jsonify([task.to_dict() for task in tasks])


@tasks_bp.post("")
@jwt_required()
def create_task():
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    plan_id = data.get("plan_id")
    if not title:
        return jsonify({"message": "任务标题不能为空"}), 400
    if plan_id and not StudyPlan.query.filter_by(id=plan_id, user_id=user_id).first():
        return jsonify({"message": "学习计划不存在"}), 404

    task = StudyTask(
        user_id=user_id,
        plan_id=plan_id,
        title=title,
        description=(data.get("description") or "").strip(),
        due_date=_parse_date(data.get("due_date")),
    )
    db.session.add(task)
    db.session.commit()
    return jsonify(task.to_dict()), 201


@tasks_bp.put("/<int:task_id>")
@jwt_required()
def update_task(task_id):
    user_id = int(get_jwt_identity())
    task = StudyTask.query.filter_by(id=task_id, user_id=user_id).first()
    if not task:
        return jsonify({"message": "任务不存在"}), 404

    data = request.get_json(silent=True) or {}
    task.title = (data.get("title") or task.title).strip()
    task.description = (data.get("description") or "").strip()
    task.due_date = _parse_date(data.get("due_date"))
    if data.get("status") in {"todo", "done"}:
        task.status = data["status"]
        task.completed_at = datetime.utcnow() if task.status == "done" else None
    db.session.commit()
    return jsonify(task.to_dict())


@tasks_bp.delete("/<int:task_id>")
@jwt_required()
def delete_task(task_id):
    user_id = int(get_jwt_identity())
    task = StudyTask.query.filter_by(id=task_id, user_id=user_id).first()
    if not task:
        return jsonify({"message": "任务不存在"}), 404
    db.session.delete(task)
    db.session.commit()
    return jsonify({"message": "删除成功"})


@tasks_bp.post("/<int:task_id>/complete")
@jwt_required()
def complete_task(task_id):
    user_id = int(get_jwt_identity())
    task = StudyTask.query.filter_by(id=task_id, user_id=user_id).first()
    if not task:
        return jsonify({"message": "任务不存在"}), 404
    task.status = "done"
    task.completed_at = datetime.utcnow()
    db.session.commit()
    return jsonify(task.to_dict())


@tasks_bp.post("/<int:task_id>/undo")
@jwt_required()
def undo_task(task_id):
    user_id = int(get_jwt_identity())
    task = StudyTask.query.filter_by(id=task_id, user_id=user_id).first()
    if not task:
        return jsonify({"message": "任务不存在"}), 404
    task.status = "todo"
    task.completed_at = None
    db.session.commit()
    return jsonify(task.to_dict())


def _parse_date(value):
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d").date()
