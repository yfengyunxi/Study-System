from datetime import datetime
from unittest.mock import patch

from extensions import db
from models.material import Material, ReindexJob


def test_reindex_job_to_dict_includes_poll_contract(app, make_user, make_material):
    user = make_user()
    material = make_material(user, status="ready")
    job = ReindexJob(
        user_id=user.id,
        material_id=material.id,
        generation=2,
        status="queued",
        phase="queued",
        progress_json='{"chunks_indexed": 0}',
    )
    db.session.add(job)
    db.session.commit()

    data = job.to_dict()

    assert data["job_id"] == job.id
    assert data["material_id"] == material.id
    assert data["generation"] == 2
    assert data["status"] == "queued"
    assert data["phase"] == "queued"
    assert data["started_at"] is None
    assert data["finished_at"] is None
    assert data["progress"] == {"chunks_indexed": 0}
    assert data["last_error"] is None
    assert data["error_code"] is None
    assert data["retryable"] is False
    assert data["poll_url"] == f"/api/materials/{material.id}/index-status"


def test_reindex_start_returns_202_job(client, auth_headers, make_material):
    headers, user = auth_headers()
    material = make_material(user, status="ready")
    material.active_index_generation = 4
    material.index_state = "ready"
    db.session.commit()

    response = client.post(f"/api/materials/{material.id}/reindex", headers=headers, json={"request_id": "reindex-1"})

    assert response.status_code == 202
    data = response.get_json()
    assert data["message"] == "索引重建已开始"
    assert data["job"]["status"] == "queued"
    assert data["job"]["generation"] == 5
    assert data["job"]["poll_url"] == f"/api/materials/{material.id}/index-status"
    assert data["material"]["index_state"] == "queued"
    assert data["material"]["active_index_generation"] == 4
    assert data["material"]["building_index_generation"] == 5


def test_duplicate_reindex_returns_existing_active_job(client, auth_headers, make_material):
    headers, user = auth_headers()
    material = make_material(user, status="ready")

    first = client.post(f"/api/materials/{material.id}/reindex", headers=headers, json={"request_id": "first"})
    second = client.post(f"/api/materials/{material.id}/reindex", headers=headers, json={"request_id": "second"})

    assert first.status_code == 202
    assert second.status_code == 202
    assert second.get_json()["message"] == "索引重建已在进行中"
    assert second.get_json()["job"]["job_id"] == first.get_json()["job"]["job_id"]


def test_reindex_status_reports_previous_generation_available(client, auth_headers, make_material):
    headers, user = auth_headers()
    material = make_material(user, status="ready")
    material.active_index_generation = 3
    material.building_index_generation = 4
    material.index_state = "queued"
    job = ReindexJob(user_id=user.id, material_id=material.id, generation=4, status="queued", phase="queued")
    db.session.add(job)
    db.session.commit()

    response = client.get(f"/api/materials/{material.id}/index-status", headers=headers)

    assert response.status_code == 200
    data = response.get_json()
    assert data["ask_ai_available"] is True
    assert data["ask_ai_uses_generation"] == 3


def test_reindex_cross_user_material_returns_404(client, auth_headers, make_user, make_material):
    headers, _user = auth_headers()
    other = make_user("other-reindex")
    material = make_material(other, status="ready")

    response = client.post(f"/api/materials/{material.id}/reindex", headers=headers, json={})

    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "MATERIAL_NOT_FOUND"


def test_reindex_success_switches_active_generation(app, make_user, make_material):
    user = make_user()
    material = make_material(user, status="ready")
    material.active_index_generation = 1
    material.building_index_generation = 2
    material.index_state = "queued"
    job = ReindexJob(user_id=user.id, material_id=material.id, generation=2, status="queued", phase="queued")
    db.session.add(job)
    db.session.commit()

    from routes.materials import _run_reindex_job

    with patch("routes.materials._process_material") as process:
        _run_reindex_job(app, job.id)

    db.session.refresh(material)
    db.session.refresh(job)
    process.assert_called_once()
    assert material.active_index_generation == 2
    assert material.building_index_generation is None
    assert material.index_state == "ready"
    assert job.status == "succeeded"


def test_reindex_failure_preserves_previous_ready_generation(app, make_user, make_material):
    user = make_user()
    material = make_material(user, status="ready")
    material.active_index_generation = 7
    material.building_index_generation = 8
    material.index_state = "queued"
    job = ReindexJob(user_id=user.id, material_id=material.id, generation=8, status="queued", phase="queued")
    db.session.add(job)
    db.session.commit()

    from routes.materials import _run_reindex_job

    with patch("routes.materials._process_material", side_effect=RuntimeError("boom")):
        _run_reindex_job(app, job.id)

    db.session.refresh(material)
    db.session.refresh(job)
    assert material.active_index_generation == 7
    assert material.building_index_generation is None
    assert material.index_state == "stale"
    assert material.status == "ready"
    assert job.status == "failed"
    assert job.error_code == "INDEX_FAILED"
    assert job.retryable is True


def test_status_marks_interrupted_running_job_stale(client, auth_headers, make_material):
    headers, user = auth_headers()
    material = make_material(user, status="ready")
    material.index_state = "running"
    material.active_index_generation = 2
    material.building_index_generation = 3
    job = ReindexJob(user_id=user.id, material_id=material.id, generation=3, status="running", phase="indexing_text")
    db.session.add(job)
    db.session.commit()

    response = client.get(f"/api/materials/{material.id}/index-status", headers=headers)

    assert response.status_code == 200
    data = response.get_json()
    assert data["job"]["status"] == "stale"
    assert data["job"]["retryable"] is True
    assert data["ask_ai_available"] is True
    assert data["ask_ai_uses_generation"] == 2
