import json

from flask import current_app

from extensions import db
from models.chat import ChatHistory, Citation, Conversation, Message


def migrate_chat_history_for_user(user_id):
    try:
        migrated = 0
        rows = ChatHistory.query.filter_by(user_id=user_id).order_by(ChatHistory.created_at.asc()).all()
        for row in rows:
            if Conversation.query.filter_by(user_id=user_id, legacy_history_id=row.id).first():
                continue
            conversation = Conversation(
                user_id=user_id,
                title=(row.question or "历史问答")[:40] or "历史问答",
                default_scope_json=_legacy_scope_json(row),
                status="active",
                legacy_history_id=row.id,
                created_at=row.created_at,
            )
            db.session.add(conversation)
            db.session.flush()
            user_message = Message(
                conversation_id=conversation.id,
                user_id=user_id,
                role="user",
                content=row.question,
                status="succeeded",
                scope_snapshot_json=conversation.default_scope_json,
                created_at=row.created_at,
            )
            assistant_message = Message(
                conversation_id=conversation.id,
                user_id=user_id,
                role="assistant",
                content=row.answer,
                status="succeeded",
                scope_snapshot_json=conversation.default_scope_json,
                parent_message_id=None,
                created_at=row.created_at,
            )
            db.session.add_all([user_message, assistant_message])
            db.session.flush()
            assistant_message.parent_message_id = user_message.id
            for citation in _citations_from_legacy(row.references_json, assistant_message.id):
                db.session.add(citation)
            migrated += 1
        db.session.commit()
        return {"migrated": migrated, "failed": False}
    except Exception:
        db.session.rollback()
        current_app.logger.warning("Failed to migrate legacy chat history", exc_info=True)
        return {"migrated": 0, "failed": True}


def _legacy_scope_json(row):
    if row.material_id:
        return json.dumps({"scope_type": "material", "material_id": row.material_id}, ensure_ascii=False)
    return json.dumps({"scope_type": "all"}, ensure_ascii=False)


def _citations_from_legacy(references_json, message_id):
    try:
        references = json.loads(references_json or "[]")
    except json.JSONDecodeError:
        references = []
    citations = []
    for item in references:
        ref_type = item.get("legacy_type") or item.get("type") or "text"
        citations.append(
            Citation(
                message_id=message_id,
                type="image" if ref_type in {"image", "visual"} else "text",
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
                preview=item.get("content_preview") or item.get("content") or "",
                score=item.get("score"),
                source_state="active",
                generation=item.get("generation"),
            )
        )
    return citations
