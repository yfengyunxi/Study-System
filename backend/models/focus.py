from datetime import date

from extensions import db
from services.time_service import utc_now


class FocusSession(db.Model):
    __tablename__ = "focus_session"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    client_session_id = db.Column(db.String(120), nullable=False)
    started_at = db.Column(db.DateTime, nullable=True)
    ended_at = db.Column(db.DateTime, nullable=True)
    duration_seconds = db.Column(db.Integer, nullable=False)
    planned_seconds = db.Column(db.Integer, nullable=False)
    study_date = db.Column(db.Date, nullable=False, index=True)
    timezone_offset_minutes = db.Column(db.Integer, nullable=False)
    source = db.Column(db.String(50), default="pomodoro", nullable=False)
    status = db.Column(db.String(20), default="completed", nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    __table_args__ = (
        db.UniqueConstraint("user_id", "client_session_id", name="uq_focus_session_user_client"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "client_session_id": self.client_session_id,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "duration_seconds": self.duration_seconds,
            "planned_seconds": self.planned_seconds,
            "study_date": self.study_date.isoformat() if self.study_date else None,
            "timezone_offset_minutes": self.timezone_offset_minutes,
            "source": self.source,
            "status": self.status or "completed",
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
