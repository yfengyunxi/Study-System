from collections import Counter
from datetime import date, datetime, timedelta

from sqlalchemy import func

from models.chat import ChatHistory, Conversation
from models.focus import FocusSession
from models.material import Material, MaterialFolder
from models.plan import StudyTask


def dashboard_stats(user_id):
    today = date.today()
    conversations = Conversation.query.filter_by(user_id=user_id, status="active").order_by(Conversation.updated_at.desc().nullslast(), Conversation.created_at.desc()).limit(5).all()
    legacy_recent = ChatHistory.query.filter_by(user_id=user_id).order_by(ChatHistory.created_at.desc()).limit(5).all()
    total_materials = Material.query.filter_by(user_id=user_id).count()
    total_chats = Conversation.query.filter_by(user_id=user_id, status="active").count() or ChatHistory.query.filter_by(user_id=user_id).count()
    total_tasks = StudyTask.query.filter_by(user_id=user_id).count()
    done_tasks = StudyTask.query.filter_by(user_id=user_id, status="done").count()
    today_tasks = StudyTask.query.filter_by(user_id=user_id, due_date=today).all()
    completion_rate = round(done_tasks / total_tasks * 100, 1) if total_tasks else 0
    recent_chat_dicts = [_conversation_recent_dict(item) for item in conversations] if conversations else [chat.to_dict() for chat in legacy_recent]

    base = {
        "generated_at": datetime.utcnow().isoformat(),
        "total_materials": total_materials,
        "total_chats": total_chats,
        "total_tasks": total_tasks,
        "done_tasks": done_tasks,
        "today_tasks": len(today_tasks),
        "today_done_tasks": len([task for task in today_tasks if task.status == "done"]),
        "completion_rate": completion_rate,
        "recent_chats": recent_chat_dicts,
        "weak_points": weak_points(user_id),
        "today_focus_seconds": today_focus_seconds(user_id, today),
        "today_checklist": {
            "items": [task.to_dict() for task in today_tasks],
            "total": len(today_tasks),
            "done": len([task for task in today_tasks if task.status == "done"]),
            "overdue": StudyTask.query.filter(StudyTask.user_id == user_id, StudyTask.status == "todo", StudyTask.due_date < today).count(),
        },
        "task_trend": task_trend(user_id),
        "focus_duration_trend": focus_duration_trend(user_id),
        "material_type_summary": material_types(user_id),
        "folder_summary": folder_material_counts(user_id),
    }
    base["knowledge_health"] = knowledge_health(user_id)
    base["active_plan_summary"] = active_plan_summary(user_id)
    actions = next_actions(user_id, legacy_recent)
    base["today_focus"] = actions[0] if actions else None
    base["next_actions"] = actions[:5]
    base["ai_continuity"] = {
        "recent_item": recent_chat_dicts[0] if recent_chat_dicts else None,
        "route": "/chat" if recent_chat_dicts else "/chat?scope_type=all",
    }
    return base


def today_focus_seconds(user_id, target_date=None):
    target_date = target_date or date.today()
    return int(
        db_scalar_sum(
            FocusSession.query.filter_by(user_id=user_id, study_date=target_date, status="completed").with_entities(
                func.coalesce(func.sum(FocusSession.duration_seconds), 0)
            )
        )
    )


def focus_duration_trend(user_id, days=7):
    days = int(days)
    start = date.today() - timedelta(days=days - 1)
    rows = (
        FocusSession.query.filter(
            FocusSession.user_id == user_id,
            FocusSession.status == "completed",
            FocusSession.study_date >= start,
        )
        .with_entities(FocusSession.study_date, func.coalesce(func.sum(FocusSession.duration_seconds), 0))
        .group_by(FocusSession.study_date)
        .all()
    )
    count_map = {day.isoformat() if hasattr(day, "isoformat") else str(day): int(seconds or 0) for day, seconds in rows}
    return [
        {"date": (start + timedelta(days=offset)).isoformat(), "duration_seconds": count_map.get((start + timedelta(days=offset)).isoformat(), 0)}
        for offset in range(days)
    ]


def db_scalar_sum(query):
    row = query.first()
    if isinstance(row, tuple):
        return row[0] or 0
    return row[0] if row else 0


def task_trend(user_id):
    start = date.today() - timedelta(days=6)
    rows = (
        StudyTask.query.filter(
            StudyTask.user_id == user_id,
            StudyTask.completed_at.isnot(None),
            func.date(StudyTask.completed_at) >= start,
        )
        .with_entities(func.date(StudyTask.completed_at), func.count(StudyTask.id))
        .group_by(func.date(StudyTask.completed_at))
        .all()
    )
    count_map = {str(day): count for day, count in rows}
    return [{"date": (start + timedelta(days=offset)).isoformat(), "count": count_map.get((start + timedelta(days=offset)).isoformat(), 0)} for offset in range(7)]


def material_types(user_id):
    rows = Material.query.filter_by(user_id=user_id).with_entities(Material.file_type, func.count(Material.id)).group_by(Material.file_type).all()
    return [{"type": file_type, "count": count} for file_type, count in rows]


def folder_material_counts(user_id):
    folders = MaterialFolder.query.filter_by(user_id=user_id).all()
    result = []
    for folder in folders:
        result.append({"folder_id": folder.id, "folder_name": folder.name, "count": Material.query.filter_by(user_id=user_id, folder_id=folder.id).count()})
    uncategorized = Material.query.filter_by(user_id=user_id, folder_id=None).count()
    if uncategorized:
        result.append({"folder_id": None, "folder_name": "未分类", "count": uncategorized})
    return result


def weak_points(user_id):
    counter = Counter()
    materials = Material.query.filter_by(user_id=user_id).all()
    for material in materials:
        for keyword in material.keywords.split(",") if material.keywords else []:
            if keyword.strip():
                counter[keyword.strip()] += 1
    unfinished = StudyTask.query.filter_by(user_id=user_id, status="todo").all()
    for task in unfinished:
        for word in task.title.replace("，", " ").replace(",", " ").split():
            if len(word.strip()) >= 2:
                counter[word.strip()] += 1
    return [{"name": name, "count": count} for name, count in counter.most_common(8)]


def knowledge_health(user_id):
    materials = Material.query.filter_by(user_id=user_id).all()
    return {
        "total": len(materials),
        "ready": len([item for item in materials if item.status == "ready"]),
        "processing": len([item for item in materials if item.status == "processing"]),
        "failed": len([item for item in materials if item.status == "failed"]),
        "uncategorized": len([item for item in materials if not item.folder_id]),
        "visual_asset_count": sum(len(item.visual_assets) for item in materials),
    }


def active_plan_summary(user_id):
    tasks = StudyTask.query.filter_by(user_id=user_id).all()
    unfinished = [task for task in tasks if task.status != "done"]
    next_due = sorted([task for task in unfinished if task.due_date], key=lambda task: task.due_date)
    total = len(tasks)
    done = len([task for task in tasks if task.status == "done"])
    return {
        "active_count": len(set(task.plan_id for task in unfinished if task.plan_id)),
        "average_progress_percent": round(done / total * 100) if total else 0,
        "next_due_task": next_due[0].to_dict() if next_due else None,
    }


def _action(type_, title, reason, priority, route, action_label):
    return {"type": type_, "title": title, "reason": reason, "priority": priority, "route": route, "action_label": action_label}


def next_actions(user_id, recent_chats):
    today = date.today()
    actions = []
    overdue = StudyTask.query.filter(StudyTask.user_id == user_id, StudyTask.status == "todo", StudyTask.due_date < today).order_by(StudyTask.due_date.asc()).limit(3).all()
    actions.extend([_action("overdue_task", task.title, "已逾期", 100, "/plans?task_scope=overdue", "处理逾期任务") for task in overdue])
    due_today = StudyTask.query.filter_by(user_id=user_id, status="todo", due_date=today).limit(3).all()
    actions.extend([_action("due_today", task.title, "今天截止", 90, "/plans?task_scope=today", "完成今日任务") for task in due_today])
    failed = Material.query.filter_by(user_id=user_id, status="failed").limit(2).all()
    actions.extend([_action("failed_material", item.title, "资料处理失败", 80, f"/materials/{item.id}", "查看失败原因") for item in failed])
    uncategorized = Material.query.filter_by(user_id=user_id, folder_id=None).limit(2).all()
    actions.extend([_action("unclassified_material", item.title, "尚未分类", 70, "/materials", "整理知识库") for item in uncategorized])
    actions.extend([_action("recent_chat", chat.question, "继续最近问答", 60, "/chat", "继续追问") for chat in recent_chats[:2]])
    ready = Material.query.filter_by(user_id=user_id, status="ready").order_by(Material.created_at.desc()).limit(2).all()
    actions.extend([_action("ready_new_material", item.title, "可开始资料问答", 50, f"/chat?scope_type=material&material_id={item.id}", "基于资料提问") for item in ready])
    if not actions:
        actions.append(_action("empty_start", "上传第一份学习资料", "开始建立个人知识库", 40, "/materials?upload=1", "上传资料"))
    actions.sort(key=lambda item: item["priority"], reverse=True)
    return actions


def _conversation_recent_dict(conversation):
    latest_user = next((message for message in reversed(conversation.messages) if message.role == "user"), None)
    latest_assistant = next((message for message in reversed(conversation.messages) if message.role == "assistant"), None)
    return {
        "id": conversation.id,
        "conversation_id": conversation.id,
        "question": latest_user.content if latest_user else conversation.title,
        "answer": latest_assistant.content if latest_assistant else "",
        "created_at": conversation.created_at.isoformat() if conversation.created_at else None,
    }
