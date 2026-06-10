from datetime import date, datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from extensions import db
from models.focus import FocusSession
from services.error_service import error_response
from services.stats_service import today_focus_seconds


focus_bp = Blueprint("focus", __name__)


@focus_bp.post("")
@jwt_required()
def create_focus_session():
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}
    try:
        payload = _validate_payload(data)
    except ValueError as exc:
        return error_response("VALIDATION_ERROR", str(exc), status=400)

    existing = FocusSession.query.filter_by(user_id=user_id, client_session_id=payload["client_session_id"]).first()
    if existing:
        return jsonify({"focus_session": existing.to_dict(), "today_focus_seconds": today_focus_seconds(user_id, existing.study_date)}), 200

    session = FocusSession(user_id=user_id, **payload)
    db.session.add(session)
    db.session.commit()
    return jsonify({"focus_session": session.to_dict(), "today_focus_seconds": today_focus_seconds(user_id, session.study_date)}), 201


def _validate_payload(data):
    client_session_id = (data.get("client_session_id") or "").strip()
    if not client_session_id:
        raise ValueError("client_session_id 不能为空")
    try:
        duration_seconds = int(data.get("duration_seconds"))
    except (TypeError, ValueError):
        raise ValueError("duration_seconds 必须是数字")
    if duration_seconds < 60 or duration_seconds > 14400:
        raise ValueError("duration_seconds 必须在 60 到 14400 秒之间")
    planned_seconds = int(data.get("planned_seconds") or duration_seconds)
    try:
        study_date = date.fromisoformat(data.get("study_date") or "")
    except ValueError:
        raise ValueError("study_date 必须是 YYYY-MM-DD")
    started_at = _parse_datetime(data.get("started_at"))
    ended_at = _parse_datetime(data.get("ended_at"))
    if started_at and ended_at:
        computed = abs((ended_at - started_at).total_seconds())
        if abs(computed - duration_seconds) > 5:
            raise ValueError("duration_seconds 与开始结束时间不匹配")
    return {
        "client_session_id": client_session_id[:120],
        "started_at": started_at,
        "ended_at": ended_at,
        "duration_seconds": duration_seconds,
        "planned_seconds": planned_seconds,
        "study_date": study_date,
        "timezone_offset_minutes": int(data.get("timezone_offset_minutes") or 0),
        "source": (data.get("source") or "pomodoro")[:50],
        "status": "completed",
    }


def _parse_datetime(value):
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed.replace(tzinfo=None)
    except ValueError:
        raise ValueError("started_at/ended_at 必须是 ISO 时间")
