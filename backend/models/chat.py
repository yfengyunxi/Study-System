import json

from services.rag_service import references_to_json
from extensions import db
from services.time_service import utc_now


class ChatHistory(db.Model):
    __tablename__ = "chat_history"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    material_id = db.Column(db.Integer, db.ForeignKey("material.id"), nullable=True, index=True)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    references_json = db.Column(db.Text, default="[]")
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    def to_dict(self):
        try:
            references = json.loads(self.references_json or "[]")
        except json.JSONDecodeError:
            references = []
        references = json.loads(references_to_json(references))
        return {
            "id": self.id,
            "user_id": self.user_id,
            "material_id": self.material_id,
            "question": self.question,
            "answer": self.answer,
            "references": references,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Conversation(db.Model):
    __tablename__ = "conversation"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    title = db.Column(db.String(200), default="新会话", nullable=False)
    default_scope_json = db.Column(db.Text, default='{"scope_type":"all"}', nullable=False)
    status = db.Column(db.String(20), default="active", nullable=False, index=True)
    legacy_history_id = db.Column(db.Integer, db.ForeignKey("chat_history.id"), nullable=True, unique=True)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)
    updated_at = db.Column(db.DateTime, onupdate=utc_now, nullable=True)
    deleted_at = db.Column(db.DateTime, nullable=True)

    messages = db.relationship(
        "Message",
        backref="conversation",
        cascade="all, delete-orphan",
        lazy=True,
        order_by="Message.created_at",
    )

    def default_scope(self):
        try:
            return json.loads(self.default_scope_json or "{}")
        except json.JSONDecodeError:
            return {"scope_type": "all"}

    def to_dict(self):
        created_at = self.created_at.isoformat() if self.created_at else None
        updated = self.updated_at or self.created_at
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "default_scope": self.default_scope(),
            "status": self.status,
            "legacy_history_id": self.legacy_history_id,
            "created_at": created_at,
            "updated_at": updated.isoformat() if updated else created_at,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }


class Message(db.Model):
    __tablename__ = "message"

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey("conversation.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    role = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, default="", nullable=False)
    status = db.Column(db.String(30), default="pending", nullable=False, index=True)
    scope_snapshot_json = db.Column(db.Text, default="{}", nullable=False)
    request_id = db.Column(db.String(120), nullable=True, index=True)
    parent_message_id = db.Column(db.Integer, db.ForeignKey("message.id"), nullable=True)
    retry_of_message_id = db.Column(db.Integer, db.ForeignKey("message.id"), nullable=True)
    error_code = db.Column(db.String(50), nullable=True)
    retryable = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)
    updated_at = db.Column(db.DateTime, onupdate=utc_now, nullable=True)

    citations = db.relationship(
        "Citation",
        backref="message",
        cascade="all, delete-orphan",
        lazy=True,
        order_by="Citation.id",
    )

    def scope_snapshot(self):
        try:
            return json.loads(self.scope_snapshot_json or "{}")
        except json.JSONDecodeError:
            return {}

    def to_dict(self, include_citations=False):
        created_at = self.created_at.isoformat() if self.created_at else None
        updated = self.updated_at or self.created_at
        data = {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "user_id": self.user_id,
            "role": self.role,
            "content": self.content,
            "status": self.status,
            "scope_snapshot": self.scope_snapshot(),
            "request_id": self.request_id,
            "parent_message_id": self.parent_message_id,
            "retry_of_message_id": self.retry_of_message_id,
            "error_code": self.error_code,
            "retryable": self.retryable,
            "created_at": created_at,
            "updated_at": updated.isoformat() if updated else created_at,
        }
        if include_citations:
            citations = [citation.to_dict() for citation in self.citations]
            data["citations"] = citations
            if self.role == "assistant":
                data["references"] = citations
        return data


class Citation(db.Model):
    __tablename__ = "citation"

    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.Integer, db.ForeignKey("message.id"), nullable=False, index=True)
    type = db.Column(db.String(20), default="text", nullable=False)
    material_id = db.Column(db.Integer, nullable=True, index=True)
    material_title_snapshot = db.Column(db.String(200), default="")
    folder_id_snapshot = db.Column(db.Integer, nullable=True)
    folder_name_snapshot = db.Column(db.String(120), default="")
    chunk_id = db.Column(db.Integer, nullable=True)
    chunk_index = db.Column(db.Integer, nullable=True)
    asset_id = db.Column(db.Integer, nullable=True)
    page_number = db.Column(db.Integer, nullable=True)
    asset_index = db.Column(db.Integer, nullable=True)
    caption = db.Column(db.String(500), default="")
    preview = db.Column(db.Text, default="")
    score = db.Column(db.Float, nullable=True)
    source_state = db.Column(db.String(20), default="active", nullable=False)
    generation = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    def to_dict(self):
        score_display = None
        if self.score is not None:
            score_display = f"相关度 {round(float(self.score) * 100)}%"
        return {
            "id": self.id,
            "type": self.type,
            "material_id": self.material_id,
            "material_title_snapshot": self.material_title_snapshot,
            "folder_id_snapshot": self.folder_id_snapshot,
            "folder_name_snapshot": self.folder_name_snapshot,
            "chunk_id": self.chunk_id,
            "chunk_index": self.chunk_index,
            "asset_id": self.asset_id,
            "page_number": self.page_number,
            "asset_index": self.asset_index,
            "caption": self.caption,
            "preview": self.preview,
            "score": self.score,
            "score_display": score_display,
            "source_state": self.source_state,
            "generation": self.generation,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
