from datetime import date, datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from sqlalchemy import case

from extensions import db
from models.plan import StudyPlan, StudyTask


tasks_bp = Blueprint("tasks", __name__)

VALID_TASK_SCOPES = {"today", "overdue", "upcoming", "unscheduled", "completed"}
VALID_TASK_STATUSES = {"todo", "done"}


@tasks_bp.get("")
@jwt_required()
def list_tasks():
    user_id = int(get_jwt_identity())
    query = StudyTask.query.filter_by(user_id=user_id)
    today = date.today()

    scope = (request.args.get("scope") or "").strip()
    status = (request.args.get("status") or "").strip()
    plan_id = request.args.get("plan_id")

    if scope and scope not in VALID_TASK_SCOPES:
        return jsonify({"message": "任务范围参数无效"}), 400
    if status and status not in VALID_TASK_STATUSES:
        return jsonify({"message": "任务状态参数无效"}), 400
    if plan_id:
        try:
            plan_id_int = int(plan_id)
        except ValueError:
            return jsonify({"message": "学习计划不存在"}), 404
        if not StudyPlan.query.filter_by(id=plan_id_int, user_id=user_id).first():
            return jsonify({"message": "学习计划不存在"}), 404
        query = query.filter_by(plan_id=plan_id_int)
    if status:
        query = query.filter_by(status=status)

    try:
        from_date = _parse_date_or_error(request.args.get("from"))
        to_date = _parse_date_or_error(request.args.get("to"))
    except ValueError as exc:
        return jsonify({"message": str(exc)}), 400
    if from_date and to_date and to_date < from_date:
        return jsonify({"message": "结束日期不能早于开始日期"}), 400
    if from_date:
        query = query.filter(StudyTask.due_date >= from_date)
    if to_date:
        query = query.filter(StudyTask.due_date <= to_date)

    if scope == "today":
        query = query.filter(StudyTask.due_date == today)
    elif scope == "overdue":
        query = query.filter(StudyTask.status == "todo", StudyTask.due_date < today)
    elif scope == "upcoming":
        query = query.filter(StudyTask.status == "todo", StudyTask.due_date > today)
    elif scope == "unscheduled":
        query = query.filter(StudyTask.status == "todo", StudyTask.due_date.is_(None))
    elif scope == "completed":
        query = query.filter(StudyTask.status == "done")

    tasks = (
        query.order_by(
            StudyTask.due_date.is_(None),
            StudyTask.due_date.asc(),
            case((StudyTask.status == "done", 1), else_=0),
            StudyTask.created_at.desc(),
        )
        .all()
    )
    return jsonify([task.to_dict() for task in tasks])


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

    try:
        due_date = _parse_date(data.get("due_date"))
    except ValueError as exc:
        return jsonify({"message": str(exc)}), 400

    task = StudyTask(
        user_id=user_id,
        plan_id=plan_id,
        title=title,
        description=(data.get("description") or "").strip(),
        due_date=due_date,
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
    try:
        task.due_date = _parse_date(data.get("due_date"))
    except ValueError as exc:
        return jsonify({"message": str(exc)}), 400
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


def _parse_date_or_error(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError("日期格式必须为 YYYY-MM-DD")


def _parse_date(value):
    return _parse_date_or_error(value)
