from datetime import datetime
import json

from extensions import db


class ChatHistory(db.Model):
    __tablename__ = "chat_history"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    material_id = db.Column(db.Integer, db.ForeignKey("material.id"), nullable=True, index=True)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    references_json = db.Column(db.Text, default="[]")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        try:
            references = json.loads(self.references_json or "[]")
        except json.JSONDecodeError:
            references = []
        return {
            "id": self.id,
            "user_id": self.user_id,
            "material_id": self.material_id,
            "question": self.question,
            "answer": self.answer,
            "references": references,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
