import pytest
from sqlalchemy import inspect

from extensions import db
from services.error_service import build_error, error_response
from services.scope_service import InvalidScopeError, normalize_scope, validate_scope_for_user
from services.schema_service import ensure_schema_compatibility


def test_build_error_envelope_contains_phase_a_shape(app):
    payload = build_error(
        code="AI_TIMEOUT",
        message="AI 响应超时，请稍后重试",
        details={"timeout_seconds": 90},
        field_errors={"content": "不能为空"},
        retryable=True,
        request_id="chat_req_1",
    )

    assert payload == {
        "message": "AI 响应超时，请稍后重试",
        "error": {
            "code": "AI_TIMEOUT",
            "message": "AI 响应超时，请稍后重试",
            "details": {"timeout_seconds": 90},
            "field_errors": {"content": "不能为空"},
            "retryable": True,
            "request_id": "chat_req_1",
        },
    }


def test_error_response_returns_json_status_and_default_fields(app):
    with app.app_context():
        response, status = error_response("INVALID_SCOPE_TYPE", "问答范围参数无效", status=400)

    assert status == 400
    data = response.get_json()
    assert data["message"] == "问答范围参数无效"
    assert data["error"]["code"] == "INVALID_SCOPE_TYPE"
    assert data["error"]["details"] == {}
    assert data["error"]["field_errors"] == {}
    assert data["error"]["retryable"] is False
    assert data["error"]["request_id"] is None


def test_normalize_scope_allows_uncategorized_public_null():
    scope = normalize_scope({"scope_type": "uncategorized", "folder_id": 123})

    assert scope == {"scope_type": "uncategorized", "folder_id": None}


@pytest.mark.parametrize(
    "payload, expected",
    [
        ({}, {"scope_type": "all"}),
        ({"scope_type": "general"}, {"scope_type": "general"}),
        ({"scope_type": "all"}, {"scope_type": "all"}),
        ({"scope_type": "folder", "folder_id": "3"}, {"scope_type": "folder", "folder_id": 3}),
        ({"scope_type": "material", "material_id": "7"}, {"scope_type": "material", "material_id": 7}),
    ],
)
def test_normalize_scope_supported_shapes(payload, expected):
    assert normalize_scope(payload) == expected


@pytest.mark.parametrize(
    "payload, message",
    [
        ({"scope_type": "folder"}, "folder_id 必须是数字"),
        ({"scope_type": "material"}, "material_id 必须是数字"),
        ({"scope_type": "bad"}, "问答范围参数无效"),
    ],
)
def test_normalize_scope_rejects_invalid_shapes(payload, message):
    with pytest.raises(InvalidScopeError) as exc:
        normalize_scope(payload)

    assert message in str(exc.value)


def test_validate_scope_material_requires_current_user_ready_material(app, make_user, make_material):
    user = make_user()
    other = make_user("other")
    material = make_material(user, status="ready")
    other_material = make_material(other, status="ready", title="other-material")
    failed_material = make_material(user, status="failed", title="failed-material")

    assert validate_scope_for_user(user.id, {"scope_type": "material", "material_id": material.id}) == {
        "scope_type": "material",
        "material_id": material.id,
    }

    with pytest.raises(InvalidScopeError) as cross_user:
        validate_scope_for_user(user.id, {"scope_type": "material", "material_id": other_material.id})
    assert cross_user.value.code == "MATERIAL_NOT_FOUND"

    with pytest.raises(InvalidScopeError) as not_ready:
        validate_scope_for_user(user.id, {"scope_type": "material", "material_id": failed_material.id})
    assert not_ready.value.code == "MATERIAL_NOT_READY"


def test_material_schema_includes_phase_a_index_fields(app, make_user, make_material):
    user = make_user()
    material = make_material(user, status="ready")

    data = material.to_dict()

    assert data["index_state"] == "ready"
    assert data["sync_state"] == "synced"
    assert data["active_index_generation"] == 1
    assert data["building_index_generation"] is None

    inspector = inspect(db.engine)
    columns = {column["name"] for column in inspector.get_columns("material")}
    assert "index_state" in columns
    assert "sync_state" in columns
    assert "active_index_generation" in columns
    assert "building_index_generation" in columns


def test_schema_compatibility_function_is_idempotent_for_phase_a_columns(app):
    ensure_schema_compatibility(app)
    ensure_schema_compatibility(app)

    inspector = inspect(db.engine)
    columns = {column["name"] for column in inspector.get_columns("material")}
    assert {
        "index_state",
        "sync_state",
        "active_index_generation",
        "building_index_generation",
    }.issubset(columns)
