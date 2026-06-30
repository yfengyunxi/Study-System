# Backend Contract and Schema Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish the stable backend contracts Phase A features depend on: JSON error envelopes, canonical scope validation, material index/sync fields, and schema compatibility.

**Architecture:** Add focused service helpers before feature endpoints consume them. Keep SQL as the canonical source of truth, add non-destructive schema compatibility for existing databases, and keep all new behavior covered by backend pytest tests without requiring frontend changes.

**Tech Stack:** Flask 3, Flask-SQLAlchemy, Flask-JWT-Extended, pytest, SQLite test database, existing `services.schema_service.ensure_schema_compatibility` startup hook.

---

## Backend dependency order

This is plan 01 and has no plan-file dependency. Later plans depend on this contract layer for stable error responses, scope parsing, and material index fields.

## Independent verification

Run from `D:\学习资料\大数据综合实践\zonghexitong\backend`:

```powershell
python -m pytest tests/test_api_contract_schema.py -v
```

Expected after implementation: all tests in `tests/test_api_contract_schema.py` pass.

## File structure and responsibilities

- Create: `backend/services/error_service.py`  
  Builds the standard JSON error envelope and Flask responses.

- Create: `backend/services/scope_service.py`  
  Normalizes and validates `general`, `all`, `folder`, `uncategorized`, and `material` scope payloads.

- Create: `backend/tests/test_api_contract_schema.py`  
  Drives error envelope shape, scope validation, and schema compatibility for material index/sync fields.

- Modify: `backend/models/material.py`  
  Adds `Material.index_state`, `Material.sync_state`, `Material.active_index_generation`, `Material.building_index_generation`, and includes them in `to_dict()`.

- Modify: `backend/services/schema_service.py`  
  Adds idempotent startup patches for the new material columns.

---

### Task 1: Add standard JSON error envelope

**Files:**
- Create: `backend/services/error_service.py`
- Test: `backend/tests/test_api_contract_schema.py`

- [ ] **Step 1: Write the failing tests**

Add these tests to `backend/tests/test_api_contract_schema.py`:

```python
from services.error_service import build_error, error_response


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
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
python -m pytest tests/test_api_contract_schema.py::test_build_error_envelope_contains_phase_a_shape tests/test_api_contract_schema.py::test_error_response_returns_json_status_and_default_fields -v
```

Expected: FAIL because `services.error_service` does not exist.

- [ ] **Step 3: Add minimal implementation**

Create `backend/services/error_service.py`:

```python
from flask import jsonify


def build_error(code, message, *, details=None, field_errors=None, retryable=False, request_id=None):
    return {
        "message": message,
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
            "field_errors": field_errors or {},
            "retryable": bool(retryable),
            "request_id": request_id,
        },
    }


def error_response(code, message, *, status=400, details=None, field_errors=None, retryable=False, request_id=None):
    return jsonify(
        build_error(
            code,
            message,
            details=details,
            field_errors=field_errors,
            retryable=retryable,
            request_id=request_id,
        )
    ), status
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```powershell
python -m pytest tests/test_api_contract_schema.py::test_build_error_envelope_contains_phase_a_shape tests/test_api_contract_schema.py::test_error_response_returns_json_status_and_default_fields -v
```

Expected: PASS.

---

### Task 2: Add canonical scope normalization and validation

**Files:**
- Create: `backend/services/scope_service.py`
- Test: `backend/tests/test_api_contract_schema.py`

- [ ] **Step 1: Write the failing tests**

Append to `backend/tests/test_api_contract_schema.py`:

```python
import pytest

from extensions import db
from models.material import Material
from services.scope_service import InvalidScopeError, normalize_scope, validate_scope_for_user


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
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
python -m pytest tests/test_api_contract_schema.py::test_normalize_scope_allows_uncategorized_public_null tests/test_api_contract_schema.py::test_validate_scope_material_requires_current_user_ready_material -v
```

Expected: FAIL because `services.scope_service` does not exist.

- [ ] **Step 3: Add implementation**

Create `backend/services/scope_service.py`:

```python
from models.material import Material, MaterialFolder


class InvalidScopeError(ValueError):
    def __init__(self, message, code="INVALID_SCOPE_TYPE", *, details=None):
        super().__init__(message)
        self.code = code
        self.details = details or {}


def _coerce_int(value, label):
    try:
        return int(value)
    except (TypeError, ValueError):
        raise InvalidScopeError(f"{label} 必须是数字", "VALIDATION_ERROR", details={label: value})


def normalize_scope(payload):
    payload = payload or {}
    scope_type = (payload.get("scope_type") or "all").strip()
    if scope_type == "general":
        return {"scope_type": "general"}
    if scope_type == "all":
        return {"scope_type": "all"}
    if scope_type == "uncategorized":
        return {"scope_type": "uncategorized", "folder_id": None}
    if scope_type == "folder":
        return {"scope_type": "folder", "folder_id": _coerce_int(payload.get("folder_id"), "folder_id")}
    if scope_type == "material":
        return {"scope_type": "material", "material_id": _coerce_int(payload.get("material_id"), "material_id")}
    raise InvalidScopeError("问答范围参数无效", "INVALID_SCOPE_TYPE", details={"scope_type": scope_type})


def validate_scope_for_user(user_id, payload):
    scope = normalize_scope(payload)
    scope_type = scope["scope_type"]
    if scope_type in {"general", "all", "uncategorized"}:
        return scope
    if scope_type == "folder":
        folder = MaterialFolder.query.filter_by(id=scope["folder_id"], user_id=user_id).first()
        if not folder:
            raise InvalidScopeError("文件夹不存在", "NOT_FOUND", details={"folder_id": scope["folder_id"]})
        return scope
    if scope_type == "material":
        material = Material.query.filter_by(id=scope["material_id"], user_id=user_id).first()
        if not material:
            raise InvalidScopeError("资料不存在", "MATERIAL_NOT_FOUND", details={"material_id": scope["material_id"]})
        if material.status != "ready" and not getattr(material, "active_index_generation", 0):
            raise InvalidScopeError("该资料尚未处理完成，暂不能用于问答", "MATERIAL_NOT_READY", details={"material_id": material.id})
        return scope
    raise InvalidScopeError("问答范围参数无效", "INVALID_SCOPE_TYPE")
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```powershell
python -m pytest tests/test_api_contract_schema.py::test_normalize_scope_supported_shapes tests/test_api_contract_schema.py::test_validate_scope_material_requires_current_user_ready_material -v
```

Expected: PASS.

---

### Task 3: Add material index and sync fields

**Files:**
- Modify: `backend/models/material.py`
- Modify: `backend/tests/conftest.py`
- Test: `backend/tests/test_api_contract_schema.py`

- [ ] **Step 1: Write the failing test**

Append to `backend/tests/test_api_contract_schema.py`:

```python
from sqlalchemy import inspect


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
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```powershell
python -m pytest tests/test_api_contract_schema.py::test_material_schema_includes_phase_a_index_fields -v
```

Expected: FAIL because the new columns and serialized fields do not exist.

- [ ] **Step 3: Update the model**

In `backend/models/material.py`, add these fields after `status`:

```python
    index_state = db.Column(db.String(20), default="not_indexed", nullable=False)
    sync_state = db.Column(db.String(20), default="synced", nullable=False)
    active_index_generation = db.Column(db.Integer, default=0, nullable=False)
    building_index_generation = db.Column(db.Integer, nullable=True)
```

In `Material.to_dict()`, add these keys near `status`:

```python
            "index_state": self.index_state,
            "sync_state": self.sync_state,
            "active_index_generation": self.active_index_generation,
            "building_index_generation": self.building_index_generation,
```

- [ ] **Step 4: Update test factories**

In `backend/tests/conftest.py`, update `make_material()` so ready test materials have a usable generation:

```python
            status=status,
            index_state="ready" if status == "ready" else "not_indexed",
            sync_state="synced",
            active_index_generation=1 if status == "ready" else 0,
```

- [ ] **Step 5: Run the test to verify it passes under fresh tables**

Run:

```powershell
python -m pytest tests/test_api_contract_schema.py::test_material_schema_includes_phase_a_index_fields -v
```

Expected: PASS.

---

### Task 4: Extend non-destructive schema compatibility

**Files:**
- Modify: `backend/services/schema_service.py`
- Test: `backend/tests/test_api_contract_schema.py`

- [ ] **Step 1: Write the failing compatibility test**

Append to `backend/tests/test_api_contract_schema.py`:

```python
from services.schema_service import ensure_schema_compatibility


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
```

- [ ] **Step 2: Run the test**

Run:

```powershell
python -m pytest tests/test_api_contract_schema.py::test_schema_compatibility_function_is_idempotent_for_phase_a_columns -v
```

Expected before implementation: FAIL on databases missing those columns or PASS on fresh `db.create_all()` only. Continue with the implementation because user databases still need compatibility.

- [ ] **Step 3: Implement compatibility additions**

In `backend/services/schema_service.py`, inside the material column checks, add statements for missing columns. For SQLite use:

```python
        if "index_state" not in columns:
            statements.append("ALTER TABLE material ADD COLUMN index_state VARCHAR(20) DEFAULT 'not_indexed' NOT NULL")
        if "sync_state" not in columns:
            statements.append("ALTER TABLE material ADD COLUMN sync_state VARCHAR(20) DEFAULT 'synced' NOT NULL")
        if "active_index_generation" not in columns:
            statements.append("ALTER TABLE material ADD COLUMN active_index_generation INTEGER DEFAULT 0 NOT NULL")
        if "building_index_generation" not in columns:
            statements.append("ALTER TABLE material ADD COLUMN building_index_generation INTEGER")
```

For MySQL use the same field names with `VARCHAR(20)` and `INT`:

```python
        if "index_state" not in columns:
            statements.append("ALTER TABLE material ADD COLUMN index_state VARCHAR(20) NOT NULL DEFAULT 'not_indexed'")
        if "sync_state" not in columns:
            statements.append("ALTER TABLE material ADD COLUMN sync_state VARCHAR(20) NOT NULL DEFAULT 'synced'")
        if "active_index_generation" not in columns:
            statements.append("ALTER TABLE material ADD COLUMN active_index_generation INT NOT NULL DEFAULT 0")
        if "building_index_generation" not in columns:
            statements.append("ALTER TABLE material ADD COLUMN building_index_generation INT NULL")
```

After executing statements, backfill existing ready materials:

```python
        db.session.execute(
            text("UPDATE material SET index_state = 'ready', active_index_generation = 1 WHERE status = 'ready' AND active_index_generation = 0")
        )
        db.session.execute(
            text("UPDATE material SET index_state = 'failed' WHERE status = 'failed' AND index_state = 'not_indexed'")
        )
```

- [ ] **Step 4: Run full plan verification**

Run:

```powershell
python -m pytest tests/test_api_contract_schema.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add backend/services/error_service.py backend/services/scope_service.py backend/models/material.py backend/services/schema_service.py backend/tests/conftest.py backend/tests/test_api_contract_schema.py
git commit -m "feat: add phase a backend contract foundation"
```

---

## Self-review checklist

- Spec coverage: covers standard JSON error envelope, canonical scope schema, public `uncategorized` scope as `folder_id: null`, material `index_state`, generation fields, and startup schema compatibility.
- Independent testability: `tests/test_api_contract_schema.py` can run without material move, reindex jobs, chat persistence, focus sessions, or frontend changes.
- Intentional deferrals: feature endpoints consume this foundation in later plan files; no user-visible UI changes are required here.
