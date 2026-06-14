import json
from datetime import date, timedelta
from unittest.mock import patch


def test_chat_general_scope_returns_empty_references(client, auth_headers):
    headers, _user = auth_headers()

    with patch("routes.chat.AIService") as fake_ai:
        fake_ai.return_value.answer.return_value = "通用回答"
        response = client.post("/api/chat", headers=headers, json={"scope_type": "general", "question": "什么是索引？"})

    assert response.status_code == 200
    data = response.get_json()
    assert data["answer"] == "通用回答"
    assert data["references"] == []


def test_chat_all_scope_requires_ready_material(client, auth_headers):
    headers, _user = auth_headers()

    response = client.post("/api/chat", headers=headers, json={"scope_type": "all", "question": "总结资料"})

    assert response.status_code == 400
    assert response.get_json()["message"] == "当前暂无可问答的资料，请先上传并处理资料，或切换为通用问答"


def test_chat_material_scope_rejects_not_ready(client, auth_headers, make_material):
    headers, user = auth_headers()
    material = make_material(user, status="processing")

    response = client.post("/api/chat", headers=headers, json={"scope_type": "material", "material_id": material.id, "question": "总结"})

    assert response.status_code == 400


def test_chat_omitted_scope_type_preserves_legacy_all_behavior(client, auth_headers, make_material):
    headers, user = auth_headers()
    make_material(user, status="ready")

    with patch("routes.chat.RAGService") as fake_rag:
        fake_rag.return_value.answer.return_value = ("旧行为回答", [])
        response = client.post("/api/chat", headers=headers, json={"question": "总结全部"})

    assert response.status_code == 200
    assert response.get_json()["answer"] == "旧行为回答"


def test_chat_references_are_normalized_in_history(app, make_user, make_chat):
    user = make_user()
    references = [{"type": "text", "material_title": "讲义", "content_preview": "a" * 301}]
    row = make_chat(user, references_json=json.dumps(references, ensure_ascii=False))

    data = row.to_dict()

    assert data["references"][0]["material_title"] == "讲义"
    assert len(data["references"][0]["content_preview"]) == 300


def test_dashboard_stats_adds_enhanced_fields(client, auth_headers, make_material, make_task, make_chat):
    headers, user = auth_headers()
    make_material(user, title="失败资料", status="failed")
    make_material(user, title="未分类资料", status="ready")
    make_task(user, title="逾期任务", due_date=date.today() - timedelta(days=1), status="todo")
    make_task(user, title="今日任务", due_date=date.today(), status="todo")
    make_chat(user, question="最近问题", answer="最近答案")

    response = client.get("/api/stats/dashboard", headers=headers)

    assert response.status_code == 200
    data = response.get_json()
    assert "today_focus" in data
    assert data["today_focus"]["type"] == "overdue_task"
    assert data["next_actions"][0]["priority"] == 100
    assert "knowledge_health" in data
    assert "active_plan_summary" in data
    assert "ai_continuity" in data
    assert "recent_chats" in data
