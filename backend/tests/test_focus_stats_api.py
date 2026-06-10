from datetime import date, datetime, timedelta

from models.focus import FocusSession


def test_focus_session_to_dict(app, make_user):
    user = make_user()
    session = FocusSession(
        user_id=user.id,
        client_session_id="pomo-1",
        started_at=datetime(2026, 6, 10, 9, 0, 0),
        ended_at=datetime(2026, 6, 10, 9, 25, 0),
        duration_seconds=1500,
        planned_seconds=1500,
        study_date=date(2026, 6, 10),
        timezone_offset_minutes=-480,
        source="pomodoro",
    )

    data = session.to_dict()

    assert data["client_session_id"] == "pomo-1"
    assert data["status"] == "completed"
    assert data["duration_seconds"] == 1500
    assert data["study_date"] == "2026-06-10"


def test_create_focus_session_and_duplicate_is_idempotent(client, auth_headers):
    headers, _user = auth_headers()
    payload = {
        "client_session_id": "pomo-dup",
        "started_at": "2026-06-10T09:00:00+08:00",
        "ended_at": "2026-06-10T09:25:00+08:00",
        "duration_seconds": 1500,
        "planned_seconds": 1500,
        "study_date": "2026-06-10",
        "timezone_offset_minutes": -480,
        "source": "pomodoro",
    }

    first = client.post("/api/focus-sessions", headers=headers, json=payload)
    second = client.post("/api/focus-sessions", headers=headers, json=payload)

    assert first.status_code == 201
    assert second.status_code == 200
    assert first.get_json()["focus_session"]["id"] == second.get_json()["focus_session"]["id"]
    assert second.get_json()["today_focus_seconds"] == 1500


def test_focus_session_validation_errors(client, auth_headers):
    headers, _user = auth_headers()
    response = client.post(
        "/api/focus-sessions",
        headers=headers,
        json={"client_session_id": "short", "duration_seconds": 30, "study_date": "2026-06-10"},
    )

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "VALIDATION_ERROR"


def test_focus_duration_trend_zero_filled_and_summed(client, auth_headers, make_focus_session):
    headers, user = auth_headers()
    target = date.today()
    make_focus_session(user, study_date=target, duration_seconds=600, client_session_id="a")
    make_focus_session(user, study_date=target, duration_seconds=900, client_session_id="b")

    response = client.get("/api/stats/focus-duration-trend?days=7", headers=headers)

    assert response.status_code == 200
    rows = response.get_json()
    assert len(rows) == 7
    assert rows[-1]["date"] == target.isoformat()
    assert rows[-1]["duration_seconds"] == 1500
    assert rows[0]["duration_seconds"] == 0


def test_focus_duration_trend_validates_days(client, auth_headers):
    headers, _user = auth_headers()

    assert client.get("/api/stats/focus-duration-trend?days=1", headers=headers).status_code == 200
    assert client.get("/api/stats/focus-duration-trend?days=30", headers=headers).status_code == 200
    assert client.get("/api/stats/focus-duration-trend?days=0", headers=headers).status_code == 400
    assert client.get("/api/stats/focus-duration-trend?days=31", headers=headers).status_code == 400
    assert client.get("/api/stats/focus-duration-trend?days=bad", headers=headers).status_code == 400


def test_dashboard_includes_focus_fields(client, auth_headers, make_focus_session):
    headers, user = auth_headers()
    make_focus_session(user, study_date=date.today(), duration_seconds=1200, client_session_id="dash")

    response = client.get("/api/stats/dashboard", headers=headers)

    assert response.status_code == 200
    data = response.get_json()
    assert data["today_focus_seconds"] == 1200
    assert "focus_duration_trend" in data
    assert "today_checklist" in data
    assert "task_trend" in data
    assert "material_type_summary" in data
    assert "folder_summary" in data
