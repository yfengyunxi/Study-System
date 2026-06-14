import pytest

from extensions import db
from models.chat import ChatHistory, Citation, Conversation, Message
from services.ai_service import AIServiceTimeoutError, UpstreamAIError


def test_conversation_message_citation_serialization(app, make_user, make_material):
    user = make_user()
    material = make_material(user, title="数据仓库", status="ready")
    conversation = Conversation(user_id=user.id, title="数据仓库复习", default_scope_json='{"scope_type":"all"}')
    db.session.add(conversation)
    db.session.flush()
    message = Message(
        conversation_id=conversation.id,
        user_id=user.id,
        role="assistant",
        content="答案",
        status="succeeded",
        scope_snapshot_json='{"scope_type":"material","material_id":1}',
        request_id="req-1",
        retryable=False,
    )
    db.session.add(message)
    db.session.flush()
    citation = Citation(
        message_id=message.id,
        type="text",
        material_id=material.id,
        material_title_snapshot=material.title,
        folder_id_snapshot=None,
        folder_name_snapshot="",
        chunk_id=1,
        chunk_index=0,
        preview="事实表围绕业务过程建立",
        score=0.82,
        source_state="active",
        generation=1,
    )
    db.session.add(citation)
    db.session.commit()

    convo_data = conversation.to_dict()
    msg_data = message.to_dict(include_citations=True)
    cite_data = citation.to_dict()

    assert convo_data["title"] == "数据仓库复习"
    assert convo_data["default_scope"] == {"scope_type": "all"}
    assert convo_data["status"] == "active"
    assert msg_data["citations"][0]["preview"] == "事实表围绕业务过程建立"
    assert msg_data["references"] == msg_data["citations"]
    assert cite_data["score_display"] == "相关度 82%"


def test_list_conversations_migrates_legacy_history_once(client, auth_headers, make_chat):
    headers, user = auth_headers()
    legacy = make_chat(user, question="什么是事实表？", answer="事实表记录业务过程")

    first = client.get("/api/chat/conversations", headers=headers)
    second = client.get("/api/chat/conversations", headers=headers)

    assert first.status_code == 200
    assert second.status_code == 200
    rows = first.get_json()["conversations"]
    assert len(rows) == 1
    assert rows[0]["legacy_history_id"] == legacy.id
    assert Conversation.query.filter_by(user_id=user.id, legacy_history_id=legacy.id).count() == 1


def test_create_and_delete_conversation(client, auth_headers):
    headers, _user = auth_headers()

    create = client.post("/api/chat/conversations", headers=headers, json={"title": "新会话", "default_scope": {"scope_type": "all"}})
    assert create.status_code == 201
    conversation_id = create.get_json()["conversation"]["id"]

    delete = client.delete(f"/api/chat/conversations/{conversation_id}", headers=headers)
    assert delete.status_code == 204

    listed = client.get("/api/chat/conversations", headers=headers)
    assert all(item["id"] != conversation_id for item in listed.get_json()["conversations"])


def test_send_message_persists_citations(client, auth_headers, make_conversation):
    headers, user = auth_headers()
    conversation = make_conversation(user)
    refs = [{"type": "text", "material_id": 3, "title": "讲义", "content": "片段", "score": 0.5}]

    class FakeRag:
        def answer(self, **kwargs):
            return "## 回答", refs

    from unittest.mock import patch

    with patch("routes.chat.RAGService", return_value=FakeRag()):
        response = client.post(
            f"/api/chat/conversations/{conversation.id}/messages",
            headers=headers,
            json={"content": "解释", "scope": {"scope_type": "all"}, "request_id": "chat-1"},
        )

    assert response.status_code == 201
    data = response.get_json()
    assert data["assistant_message"]["status"] == "succeeded"
    assert data["assistant_message"]["citations"][0]["preview"] == "片段"
    assert Message.query.filter_by(conversation_id=conversation.id).count() == 2


def test_send_message_request_id_is_idempotent(client, auth_headers, make_conversation):
    headers, user = auth_headers()
    conversation = make_conversation(user)

    class FakeAi:
        def answer(self, question, contexts, conversation=None):
            return "回答"

    from unittest.mock import patch

    with patch("routes.chat.AIService", return_value=FakeAi()):
        first = client.post(
            f"/api/chat/conversations/{conversation.id}/messages",
            headers=headers,
            json={"content": "解释", "scope": {"scope_type": "general"}, "request_id": "same"},
        )
        second = client.post(
            f"/api/chat/conversations/{conversation.id}/messages",
            headers=headers,
            json={"content": "解释", "scope": {"scope_type": "general"}, "request_id": "same"},
        )

    assert first.status_code == 201
    assert second.status_code == 200
    assert first.get_json()["assistant_message"]["id"] == second.get_json()["assistant_message"]["id"]
    assert Message.query.filter_by(conversation_id=conversation.id).count() == 2


def test_ai_timeout_saves_failed_assistant_and_returns_504(client, auth_headers, make_conversation):
    headers, user = auth_headers()
    conversation = make_conversation(user)

    class TimeoutAi:
        def answer(self, question, contexts, conversation=None):
            raise AIServiceTimeoutError("timeout")

    from unittest.mock import patch

    with patch("routes.chat.AIService", return_value=TimeoutAi()):
        response = client.post(
            f"/api/chat/conversations/{conversation.id}/messages",
            headers=headers,
            json={"content": "解释", "scope": {"scope_type": "general"}, "request_id": "timeout"},
        )

    assert response.status_code == 504
    data = response.get_json()
    assert data["error"]["code"] == "AI_TIMEOUT"
    assert data["assistant_message"]["status"] == "failed_timeout"
    assert data["assistant_message"]["retryable"] is True


def test_upstream_error_saves_failed_assistant_and_returns_502(client, auth_headers, make_conversation):
    headers, user = auth_headers()
    conversation = make_conversation(user)

    class BrokenAi:
        def answer(self, question, contexts, conversation=None):
            raise UpstreamAIError("bad gateway")

    from unittest.mock import patch

    with patch("routes.chat.AIService", return_value=BrokenAi()):
        response = client.post(
            f"/api/chat/conversations/{conversation.id}/messages",
            headers=headers,
            json={"content": "解释", "scope": {"scope_type": "general"}, "request_id": "upstream"},
        )

    assert response.status_code == 502
    data = response.get_json()
    assert data["error"]["code"] == "UPSTREAM_AI_ERROR"
    assert data["assistant_message"]["status"] == "failed_error"


def test_retry_failed_assistant_creates_new_attempt(client, auth_headers, make_conversation, make_message):
    headers, user = auth_headers()
    conversation = make_conversation(user)
    user_message = make_message(conversation, role="user", content="解释")
    failed = make_message(
        conversation,
        role="assistant",
        content="",
        status="failed_timeout",
        parent_message_id=user_message.id,
        retryable=True,
        error_code="AI_TIMEOUT",
        scope_snapshot_json='{"scope_type":"general"}',
    )

    class FakeAi:
        def answer(self, question, contexts, conversation=None):
            return "重试成功"

    from unittest.mock import patch

    with patch("routes.chat.AIService", return_value=FakeAi()):
        response = client.post(f"/api/chat/messages/{failed.id}/retry", headers=headers, json={"request_id": "retry-1"})

    assert response.status_code == 201
    data = response.get_json()
    assert data["assistant_message"]["content"] == "重试成功"
    assert data["assistant_message"]["retry_of_message_id"] == failed.id


def test_legacy_chat_success_shape_remains_compatible(client, auth_headers):
    headers, _user = auth_headers()

    class FakeAi:
        def answer(self, question, contexts, conversation=None):
            return "通用回答"

    from unittest.mock import patch

    with patch("routes.chat.AIService", return_value=FakeAi()):
        response = client.post("/api/chat", headers=headers, json={"scope_type": "general", "question": "什么是索引？"})

    assert response.status_code == 200
    data = response.get_json()
    assert data["answer"] == "通用回答"
    assert data["references"] == []
    assert "conversation_id" in data
