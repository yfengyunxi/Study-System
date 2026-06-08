from collections import Counter
from datetime import date, timedelta

from sqlalchemy import func

from models.chat import ChatHistory
from models.material import Material, MaterialFolder
from models.plan import StudyTask


def dashboard_stats(user_id):
    today = date.today()
    total_materials = Material.query.filter_by(user_id=user_id).count()
    total_chats = ChatHistory.query.filter_by(user_id=user_id).count()
    total_tasks = StudyTask.query.filter_by(user_id=user_id).count()
    done_tasks = StudyTask.query.filter_by(user_id=user_id, status="done").count()
    today_tasks = StudyTask.query.filter_by(user_id=user_id, due_date=today).all()
    completion_rate = round(done_tasks / total_tasks * 100, 1) if total_tasks else 0

    recent_chats = (
        ChatHistory.query.filter_by(user_id=user_id)
        .order_by(ChatHistory.created_at.desc())
        .limit(5)
        .all()
    )

    return {
        "total_materials": total_materials,
        "total_chats": total_chats,
        "total_tasks": total_tasks,
        "done_tasks": done_tasks,
        "today_tasks": len(today_tasks),
        "today_done_tasks": len([task for task in today_tasks if task.status == "done"]),
        "completion_rate": completion_rate,
        "recent_chats": [chat.to_dict() for chat in recent_chats],
        "weak_points": weak_points(user_id),
    }


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
    return [
        {
            "date": (start + timedelta(days=offset)).isoformat(),
            "count": count_map.get((start + timedelta(days=offset)).isoformat(), 0),
        }
        for offset in range(7)
    ]


def material_types(user_id):
    rows = (
        Material.query.filter_by(user_id=user_id)
        .with_entities(Material.file_type, func.count(Material.id))
        .group_by(Material.file_type)
        .all()
    )
    return [{"type": file_type, "count": count} for file_type, count in rows]


def folder_material_counts(user_id):
    folders = MaterialFolder.query.filter_by(user_id=user_id).all()
    result = []
    for folder in folders:
        result.append(
            {
                "folder_id": folder.id,
                "folder_name": folder.name,
                "count": Material.query.filter_by(user_id=user_id, folder_id=folder.id).count(),
            }
        )
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
