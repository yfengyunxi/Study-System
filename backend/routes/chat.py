from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from extensions import db
from models.chat import ChatHistory
from services.ai_service import AIService
from services.rag_service import RAGService, references_to_json


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


@chat_bp.post("")
@jwt_required()
def chat():
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}
    question = (data.get("question") or "").strip()
    material_id = data.get("material_id")
    folder_id = data.get("folder_id")
    conversation = data.get("conversation") or []
    if not question:
        return jsonify({"message": "问题不能为空"}), 400

    try:
        material_id = int(material_id) if material_id else None
        folder_id = int(folder_id) if folder_id else None
        answer, references = RAGService().answer(
            user_id=user_id,
            question=question,
            material_id=material_id,
            folder_id=folder_id,
            conversation=_clean_conversation(conversation),
        )
    except ValueError as exc:
        return jsonify({"message": str(exc)}), 400
    except Exception as exc:
        current_app.logger.exception("AI chat failed")
        return jsonify({"message": f"AI 问答失败：{exc}"}), 500

    history = ChatHistory(
        user_id=user_id,
        material_id=material_id,
        question=question,
        answer=answer,
        references_json=references_to_json(references),
    )
    db.session.add(history)
    db.session.commit()
    return jsonify(history.to_dict())


@chat_bp.get("/history")
@jwt_required()
def history():
    user_id = int(get_jwt_identity())
    rows = (
        ChatHistory.query.filter_by(user_id=user_id)
        .order_by(ChatHistory.created_at.desc())
        .limit(100)
        .all()
    )
    return jsonify([item.to_dict() for item in rows])


@chat_bp.get("/history/<int:history_id>")
@jwt_required()
def history_detail(history_id):
    user_id = int(get_jwt_identity())
    row = ChatHistory.query.filter_by(id=history_id, user_id=user_id).first()
    if not row:
        return jsonify({"message": "问答记录不存在"}), 404
    return jsonify(row.to_dict())


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
