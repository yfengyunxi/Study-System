import json

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from extensions import db
from models.chat import ChatHistory, Citation, Conversation, Message
from services.ai_service import AIService, AIServiceTimeoutError, UpstreamAIError
from services.chat_history_adapter import migrate_chat_history_for_user
from services.error_service import build_error, error_response
from services.rag_service import RAGService, references_to_json
from services.scope_service import InvalidScopeError, validate_scope_for_user
from services.time_service import utc_now


chat_bp = Blueprint("chat", __name__)


@chat_bp.get("/status")
@jwt_required()
def ai_status():
    ai = AIService()
    return jsonify(
        {
            "chat_base_url": ai.chat_base_url,
            "chat_model": ai.chat_model,
            "chat_wire_api": ai.chat_wire_api,
            "chat_enabled": ai.enabled,
            "embedding_model": ai.embedding_model,
            "multimodal_embedding_model": ai.multimodal_embedding_model,
            "multimodal_enabled": ai.multimodal_enabled,
        }
    )


@chat_bp.get("/conversations")
@jwt_required()
def list_conversations():
    user_id = int(get_jwt_identity())
    migration = migrate_chat_history_for_user(user_id)
    page = max(int(request.args.get("page", 1) or 1), 1)
    limit = min(max(int(request.args.get("limit", 30) or 30), 1), 100)
    query = Conversation.query.filter_by(user_id=user_id, status="active").order_by(Conversation.created_at.desc())
    rows = query.offset((page - 1) * limit).limit(limit).all()
    return jsonify({"conversations": [row.to_dict() for row in rows], "legacy_warning": migration.get("failed", False)})


@chat_bp.post("/conversations")
@jwt_required()
def create_conversation():
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "新会话").strip()[:200] or "新会话"
    scope = data.get("default_scope") or {"scope_type": "all"}
    try:
        normalized_scope = validate_scope_for_user(user_id, scope)
    except InvalidScopeError as exc:
        return error_response(exc.code, str(exc), status=400, details=exc.details)
    conversation = Conversation(user_id=user_id, title=title, default_scope_json=json.dumps(normalized_scope, ensure_ascii=False))
    db.session.add(conversation)
    db.session.commit()
    return jsonify({"conversation": conversation.to_dict()}), 201


@chat_bp.delete("/conversations/<int:conversation_id>")
@jwt_required()
def delete_conversation(conversation_id):
    user_id = int(get_jwt_identity())
    conversation = Conversation.query.filter_by(id=conversation_id, user_id=user_id, status="active").first()
    if not conversation:
        return error_response("NOT_FOUND", "会话不存在", status=404)
    conversation.status = "deleted"
    conversation.deleted_at = utc_now()
    Message.query.filter_by(conversation_id=conversation.id, status="generating").update(
        {"status": "cancelled", "retryable": False}
    )
    db.session.commit()
    return "", 204


@chat_bp.get("/conversations/<int:conversation_id>/messages")
@jwt_required()
def list_messages(conversation_id):
    user_id = int(get_jwt_identity())
    conversation = Conversation.query.filter_by(id=conversation_id, user_id=user_id, status="active").first()
    if not conversation:
        return error_response("NOT_FOUND", "会话不存在", status=404)
    page = max(int(request.args.get("page", 1) or 1), 1)
    limit = min(max(int(request.args.get("limit", 50) or 50), 1), 100)
    rows = (
        Message.query.filter_by(conversation_id=conversation.id, user_id=user_id)
        .order_by(Message.created_at.asc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )
    return jsonify({"messages": [row.to_dict(include_citations=True) for row in rows]})


@chat_bp.post("/conversations/<int:conversation_id>/messages")
@jwt_required()
def send_conversation_message(conversation_id):
    user_id = int(get_jwt_identity())
    conversation = Conversation.query.filter_by(id=conversation_id, user_id=user_id, status="active").first()
    if not conversation:
        return error_response("NOT_FOUND", "会话不存在", status=404)
    data = request.get_json(silent=True) or {}
    content = (data.get("content") or "").strip()
    request_id = (data.get("request_id") or "")[:120]
    if not content:
        return error_response("VALIDATION_ERROR", "问题不能为空", status=400, field_errors={"content": "required"})
    existing = _message_pair_for_request(conversation.id, request_id)
    if existing:
        return jsonify(existing), 200
    try:
        scope = validate_scope_for_user(user_id, data.get("scope") or conversation.default_scope())
    except InvalidScopeError as exc:
        return error_response(exc.code, str(exc), status=400, details=exc.details)
    return _create_message_attempt(conversation, content, scope, request_id=request_id)


@chat_bp.post("/messages/<int:message_id>/retry")
@jwt_required()
def retry_message(message_id):
    user_id = int(get_jwt_identity())
    failed = Message.query.filter_by(id=message_id, user_id=user_id, role="assistant").first()
    if not failed or failed.status not in {"failed_timeout", "failed_error"}:
        return error_response("CONFLICT", "该消息不能重试", status=409)
    conversation = Conversation.query.filter_by(id=failed.conversation_id, user_id=user_id, status="active").first()
    if not conversation:
        return error_response("NOT_FOUND", "会话不存在", status=404)
    data = request.get_json(silent=True) or {}
    request_id = (data.get("request_id") or "")[:120]
    if request_id:
        existing = Message.query.filter_by(conversation_id=conversation.id, user_id=user_id, request_id=request_id, role="assistant").first()
        if existing:
            return jsonify({"conversation_id": conversation.id, "assistant_message": existing.to_dict(include_citations=True)}), 200
    parent = db.session.get(Message, failed.parent_message_id) if failed.parent_message_id else None
    content = parent.content if parent else ""
    scope = failed.scope_snapshot()
    return _create_assistant_retry(conversation, failed, content, scope, request_id=request_id)


@chat_bp.post("")
@jwt_required()
def chat():
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}
    question = (data.get("question") or "").strip()
    material_id = data.get("material_id")
    folder_id = data.get("folder_id")
    scope_type = (data.get("scope_type") or "").strip()
    conversation = data.get("conversation") or []
    if not question:
        return jsonify({"message": "问题不能为空"}), 400

    try:
        material_id = int(material_id) if material_id else None
        folder_id = int(folder_id) if folder_id else None
        if not scope_type:
            if material_id:
                scope_type = "material"
            elif folder_id:
                scope_type = "folder"
            else:
                scope_type = "all"
        scope = {"scope_type": scope_type}
        if material_id:
            scope["material_id"] = material_id
        if folder_id:
            scope["folder_id"] = folder_id
        scope = validate_scope_for_user(user_id, scope)
        scope_type = scope["scope_type"]
        material_id = scope.get("material_id")
        folder_id = scope.get("folder_id")
        if scope_type == "general":
            answer = AIService().answer(question, [], conversation=_clean_conversation(conversation))
            references = []
        else:
            answer, references = RAGService().answer(
                user_id=user_id,
                question=question,
                scope_type=scope_type,
                material_id=material_id,
                folder_id=folder_id,
                conversation=_clean_conversation(conversation),
            )
    except InvalidScopeError as exc:
        return error_response(exc.code, str(exc), status=400, details=exc.details)
    except ValueError as exc:
        return jsonify({"message": str(exc)}), 400
    except AIServiceTimeoutError:
        return error_response("AI_TIMEOUT", "AI 响应超时，可重试或继续提问", status=504, retryable=True)
    except UpstreamAIError:
        return error_response("UPSTREAM_AI_ERROR", "AI 服务暂时不可用", status=502, retryable=True)
    except Exception as exc:
        current_app.logger.exception("AI chat failed")
        return jsonify({"message": f"AI 问答失败：{exc}"}), 500

    history = ChatHistory(user_id=user_id, material_id=material_id, question=question, answer=answer, references_json=references_to_json(references))
    db.session.add(history)
    db.session.flush()
    conversation_row = Conversation(user_id=user_id, title=question[:40] or "新会话", default_scope_json=json.dumps(scope, ensure_ascii=False), legacy_history_id=history.id)
    db.session.add(conversation_row)
    db.session.flush()
    user_message = Message(conversation_id=conversation_row.id, user_id=user_id, role="user", content=question, status="succeeded", scope_snapshot_json=json.dumps(scope, ensure_ascii=False))
    assistant_message = Message(conversation_id=conversation_row.id, user_id=user_id, role="assistant", content=answer, status="succeeded", scope_snapshot_json=json.dumps(scope, ensure_ascii=False))
    db.session.add_all([user_message, assistant_message])
    db.session.flush()
    assistant_message.parent_message_id = user_message.id
    _save_citations(assistant_message, references)
    db.session.commit()
    data = history.to_dict()
    data["conversation_id"] = conversation_row.id
    data["assistant_message_id"] = assistant_message.id
    return jsonify(data)


@chat_bp.get("/history")
@jwt_required()
def history():
    user_id = int(get_jwt_identity())
    migrate_chat_history_for_user(user_id)
    rows = ChatHistory.query.filter_by(user_id=user_id).order_by(ChatHistory.created_at.desc()).limit(100).all()
    return jsonify([item.to_dict() for item in rows])


@chat_bp.get("/history/<int:history_id>")
@jwt_required()
def history_detail(history_id):
    user_id = int(get_jwt_identity())
    row = ChatHistory.query.filter_by(id=history_id, user_id=user_id).first()
    if not row:
        return jsonify({"message": "问答记录不存在"}), 404
    return jsonify(row.to_dict())


def _create_message_attempt(conversation, content, scope, request_id=None):
    user_message = Message(
        conversation_id=conversation.id,
        user_id=conversation.user_id,
        role="user",
        content=content,
        status="succeeded",
        scope_snapshot_json=json.dumps(scope, ensure_ascii=False),
        request_id=request_id,
    )
    assistant = Message(
        conversation_id=conversation.id,
        user_id=conversation.user_id,
        role="assistant",
        content="",
        status="generating",
        scope_snapshot_json=json.dumps(scope, ensure_ascii=False),
        retryable=False,
    )
    db.session.add_all([user_message, assistant])
    db.session.flush()
    assistant.parent_message_id = user_message.id
    return _complete_assistant(conversation, user_message, assistant, content, scope, request_id=request_id, status_code=201)


def _create_assistant_retry(conversation, failed, content, scope, request_id=None):
    assistant = Message(
        conversation_id=conversation.id,
        user_id=conversation.user_id,
        role="assistant",
        content="",
        status="generating",
        scope_snapshot_json=json.dumps(scope, ensure_ascii=False),
        parent_message_id=failed.parent_message_id,
        retry_of_message_id=failed.id,
        request_id=request_id,
    )
    db.session.add(assistant)
    db.session.flush()
    parent = db.session.get(Message, failed.parent_message_id) if failed.parent_message_id else None
    return _complete_assistant(conversation, parent, assistant, content, scope, request_id=request_id, status_code=201)


def _complete_assistant(conversation, user_message, assistant, content, scope, request_id=None, status_code=201):
    try:
        if scope["scope_type"] == "general":
            answer = AIService().answer(content, [], conversation=_conversation_context(conversation.id))
            references = []
        else:
            answer, references = RAGService().answer(
                user_id=conversation.user_id,
                question=content,
                scope_type=scope.get("scope_type"),
                material_id=scope.get("material_id"),
                folder_id=scope.get("folder_id"),
                conversation=_conversation_context(conversation.id),
            )
        db.session.refresh(conversation)
        if conversation.status == "deleted":
            assistant.status = "cancelled"
            assistant.retryable = False
            db.session.commit()
            return error_response("CONFLICT", "会话已删除", status=409)
        assistant.content = answer
        assistant.status = "succeeded"
        assistant.retryable = False
        _save_citations(assistant, references)
        conversation.updated_at = utc_now()
        db.session.commit()
        payload = {"conversation_id": conversation.id, "assistant_message": assistant.to_dict(include_citations=True)}
        if user_message:
            payload["user_message"] = user_message.to_dict(include_citations=True)
        return jsonify(payload), status_code
    except AIServiceTimeoutError:
        return _mark_assistant_failed(conversation, user_message, assistant, "failed_timeout", "AI_TIMEOUT", "AI 响应超时，可重试或继续提问", 504, request_id)
    except UpstreamAIError:
        return _mark_assistant_failed(conversation, user_message, assistant, "failed_error", "UPSTREAM_AI_ERROR", "AI 服务暂时不可用", 502, request_id)


def _mark_assistant_failed(conversation, user_message, assistant, status, code, message, http_status, request_id):
    assistant.status = status
    assistant.error_code = code
    assistant.retryable = True
    db.session.commit()
    payload = build_error(code, message, retryable=True, request_id=request_id)
    payload.update(
        {
            "conversation_id": conversation.id,
            "assistant_message": assistant.to_dict(include_citations=True),
        }
    )
    if user_message:
        payload["user_message"] = user_message.to_dict(include_citations=True)
    return jsonify(payload), http_status


def _message_pair_for_request(conversation_id, request_id):
    if not request_id:
        return None
    user_message = Message.query.filter_by(conversation_id=conversation_id, request_id=request_id, role="user").first()
    if not user_message:
        return None
    assistant = Message.query.filter_by(conversation_id=conversation_id, parent_message_id=user_message.id, role="assistant").first()
    return {
        "conversation_id": conversation_id,
        "user_message": user_message.to_dict(include_citations=True),
        "assistant_message": assistant.to_dict(include_citations=True) if assistant else None,
    }


def _save_citations(message, references):
    for item in references or []:
        ref_type = item.get("type") or "text"
        citation = Citation(
            message_id=message.id,
            type="image" if ref_type == "image" else "text",
            material_id=item.get("material_id"),
            material_title_snapshot=item.get("material_title") or item.get("title") or "",
            folder_id_snapshot=item.get("folder_id"),
            folder_name_snapshot=item.get("folder_name") or "",
            chunk_id=item.get("chunk_id"),
            chunk_index=item.get("chunk_index"),
            asset_id=item.get("asset_id"),
            page_number=item.get("page_number"),
            asset_index=item.get("asset_index"),
            caption=item.get("caption") or "",
            preview=item.get("content_preview") or item.get("content") or item.get("preview") or "",
            score=item.get("score"),
            source_state=item.get("source_state") or "active",
            generation=item.get("generation"),
        )
        db.session.add(citation)


def _conversation_context(conversation_id):
    rows = Message.query.filter_by(conversation_id=conversation_id).order_by(Message.created_at.desc()).limit(8).all()
    return [{"role": row.role, "content": row.content} for row in reversed(rows) if row.status == "succeeded"]


def _clean_conversation(conversation):
    cleaned = []
    if not isinstance(conversation, list):
        return cleaned
    for item in conversation[-8:]:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        content = (item.get("content") or "").strip()
        if role not in {"user", "assistant"} or not content:
            continue
        cleaned.append({"role": role, "content": content[:1200]})
    return cleaned
