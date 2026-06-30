from datetime import date, timedelta

from services.time_service import utc_now

from extensions import db


def test_plan_to_dict_includes_computed_fields(app, make_user, make_plan, make_task):
    user = make_user()
    plan = make_plan(user, title="数据库复习")
    make_task(user, plan=plan, title="已完成", status="done", completed_at=utc_now())
    make_task(user, plan=plan, title="待完成", due_date=date.today() + timedelta(days=1), status="todo")

    data = plan.to_dict(include_tasks=True)

    assert data["task_count"] == 2
    assert data["done_count"] == 1
    assert data["todo_count"] == 1
    assert data["progress_percent"] == 50
    assert data["next_due_task"]["title"] == "待完成"
    assert data["status"] == "active"
    assert data["tasks"][0]["plan_title"] == "数据库复习"


def test_plan_status_priority(app, make_user, make_plan, make_task):
    user = make_user()
    completed = make_plan(user, title="完成计划")
    make_task(user, plan=completed, status="done", completed_at=utc_now())
    overdue = make_plan(user, title="逾期计划")
    make_task(user, plan=overdue, status="todo", due_date=date.today() - timedelta(days=1))
    empty = make_plan(user, title="空计划")
    future = make_plan(user, title="未来计划", start_date=date.today() + timedelta(days=3))

    assert completed.to_dict(include_tasks=True)["status"] == "completed"
    assert overdue.to_dict(include_tasks=True)["status"] == "overdue"
    assert empty.to_dict(include_tasks=True)["status"] == "empty"
    assert future.to_dict(include_tasks=True)["status"] == "empty"


def test_get_tasks_scopes_and_filters(client, auth_headers, make_plan, make_task):
    headers, user = auth_headers()
    plan = make_plan(user)
    today = make_task(user, plan=plan, title="今天", due_date=date.today(), status="todo")
    overdue = make_task(user, plan=plan, title="逾期", due_date=date.today() - timedelta(days=1), status="todo")
    upcoming = make_task(user, plan=plan, title="未来", due_date=date.today() + timedelta(days=2), status="todo")
    unscheduled = make_task(user, plan=plan, title="未安排", due_date=None, status="todo")
    done = make_task(user, plan=plan, title="已完成", due_date=date.today(), status="done", completed_at=utc_now())

    assert [row["id"] for row in client.get("/api/tasks?scope=today", headers=headers).get_json()] == [today.id, done.id]
    assert [row["id"] for row in client.get("/api/tasks?scope=overdue", headers=headers).get_json()] == [overdue.id]
    assert [row["id"] for row in client.get("/api/tasks?scope=upcoming", headers=headers).get_json()] == [upcoming.id]
    assert [row["id"] for row in client.get("/api/tasks?scope=unscheduled", headers=headers).get_json()] == [unscheduled.id]
    assert [row["id"] for row in client.get("/api/tasks?scope=completed", headers=headers).get_json()] == [done.id]


def test_task_date_validation_returns_400(client, auth_headers):
    headers, _user = auth_headers()

    response = client.post("/api/tasks", headers=headers, json={"title": "坏日期", "due_date": "2026/06/08"})

    assert response.status_code == 400
    assert response.get_json()["message"] == "日期格式必须为 YYYY-MM-DD"


def test_plan_date_validation_returns_400(client, auth_headers):
    headers, _user = auth_headers()

    response = client.post("/api/plans", headers=headers, json={"title": "坏日期", "start_date": "2026-06-10", "end_date": "2026-06-01"})

    assert response.status_code == 400
    assert response.get_json()["message"] == "结束日期不能早于开始日期"


def test_task_plan_id_is_user_scoped(client, auth_headers, make_user, make_plan):
    headers, _user = auth_headers()
    other = make_user("other")
    other_plan = make_plan(other)

    response = client.get(f"/api/tasks?plan_id={other_plan.id}", headers=headers)

    assert response.status_code == 404
