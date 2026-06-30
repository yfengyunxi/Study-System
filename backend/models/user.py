from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db
from services.time_service import utc_now


class User(db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    nickname = db.Column(db.String(80), nullable=False)
    avatar = db.Column(db.String(255), default="")
    study_goal = db.Column(db.String(255), default="")
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        avatar = self.avatar or ""
        # If it's a local avatar path (not a full URL), keep as-is
        return {
            "id": self.id,
            "username": self.username,
            "nickname": self.nickname,
            "avatar": avatar,
            "study_goal": self.study_goal,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
