# Backend Contracts and Materials Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish Phase A backend contracts for errors/scopes/material index state, then implement material move, SQL-first RAG consistency, observable reindex jobs, and image asset error envelopes.

**Architecture:** This plan consolidates the existing 2026-06-09 backend split plans into one 2026-06-10 executable child plan. SQL remains canonical; Chroma/vector metadata is a projection that can be refreshed or marked stale. Reindex uses persisted jobs and two-generation safety so the previous ready generation remains usable until a new generation succeeds.

**Tech Stack:** Flask, Flask-JWT-Extended, Flask-SQLAlchemy, pytest, SQLite test database, existing RAG/vector services, in-process background worker.

---

## Source plans absorbed

Use these existing detailed plans as implementation detail sources; do not execute the old combined `2026-06-09-02-materials-move-and-reindex.md` because it overlaps with the split plans below.

1. `D:\学习资料\大数据综合实践\zonghexitong\docs\superpowers\plans\2026-06-09-01-backend-contract-schema-foundation.md`
2. `D:\学习资料\大数据综合实践\zonghexitong\docs\superpowers\plans\2026-06-09-02-material-move-rag-scope-consistency.md`
3. `D:\学习资料\大数据综合实践\zonghexitong\docs\superpowers\plans\2026-06-09-03-reindex-job-observability.md`

## File structure and responsibilities

- Create: `backend/services/error_service.py` — standard `{ message, error: { code, message, details, field_errors, retryable, request_id } }` envelope.
- Create: `backend/services/scope_service.py` — canonical `general/all/folder/uncategorized/material` scope normalization and user-scoped validation.
- Create: `backend/tests/test_api_contract_schema.py` — error envelope, scope validation, material schema compatibility tests.
- Create: `backend/tests/test_material_move_scope.py` — move endpoint, folder delete reconciliation, RAG folder scope tests.
- Create: `backend/tests/test_reindex_jobs.py` — reindex job/status/two-generation/stale behavior tests.
- Modify: `backend/models/material.py` — add `index_state`, `sync_state`, generation fields, and `ReindexJob`.
- Modify: `backend/models/__init__.py` — export `ReindexJob`.
- Modify: `backend/routes/materials.py` — add move endpoint, reindex 202 endpoint, index-status endpoint, image error envelopes.
- Modify: `backend/routes/folders.py` — mark moved materials stale/sync-pending on folder delete.
- Modify: `backend/services/rag_service.py` — sync folder metadata projection and validate fallback retrieval against live SQL.
- Modify: `backend/services/vector_store_service.py` — support metadata updates by query where supported.
- Modify: `backend/services/schema_service.py` — non-destructive compatibility for new material columns and reindex job table.
- Modify: `backend/tests/conftest.py` — ready materials should default to usable index generation.

## Dependency rule

Complete this whole backend plan before `2026-06-10-frontend-materials-chat-dashboard-plan.md` consumes material move/reindex contracts.

---

### Task 1: Error envelope, scope schema, material index fields

**Files:**
- Create: `backend/services/error_service.py`
- Create: `backend/services/scope_service.py`
- Create: `backend/tests/test_api_contract_schema.py`
- Modify: `backend/models/material.py`
- Modify: `backend/services/schema_service.py`
- Modify: `backend/tests/conftest.py`

- [ ] **Step 1: Execute detailed source plan task group**

Follow all tasks in:

```text
D:\学习资料\大数据综合实践\zonghexitong\docs\superpowers\plans\2026-06-09-01-backend-contract-schema-foundation.md
```

Required behaviors:

- `build_error()` returns the Phase A envelope.
- `error_response()` returns Flask JSON and status.
- `normalize_scope()` supports `{scope_type: general|all|folder|uncategorized|material}`.
- `uncategorized` always serializes as `{ "scope_type": "uncategorized", "folder_id": null }`.
- `validate_scope_for_user()` rejects cross-user and not-ready material scopes with stable codes.
- `Material.to_dict()` includes `index_state`, `sync_state`, `active_index_generation`, `building_index_generation`.
- `ensure_schema_compatibility(app)` adds missing material columns idempotently and backfills ready/failed rows.

- [ ] **Step 2: Verify contract/schema tests**

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong\backend"
python -m pytest tests\test_api_contract_schema.py -v
Pop-Location
```

Expected: PASS.

- [ ] **Step 3: Commit**

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong"
git add backend/services/error_service.py backend/services/scope_service.py backend/models/material.py backend/services/schema_service.py backend/tests/conftest.py backend/tests/test_api_contract_schema.py
git commit -m @'
feat: add phase a backend contract foundation

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
'@
Pop-Location
```

---

### Task 2: Material move endpoint and SQL/RAG consistency

**Files:**
- Create: `backend/tests/test_material_move_scope.py`
- Modify: `backend/routes/materials.py`
- Modify: `backend/routes/folders.py`
- Modify: `backend/services/rag_service.py`
- Modify: `backend/services/vector_store_service.py`

- [ ] **Step 1: Execute detailed source plan task group**

Follow all backend tasks in:

```text
D:\学习资料\大数据综合实践\zonghexitong\docs\superpowers\plans\2026-06-09-02-material-move-rag-scope-consistency.md
```

Required behaviors:

- `PATCH /api/materials/<id>/folder` supports moving to a user folder and moving to uncategorized with `folder_id: null`.
- Same-target move returns `200`, `changed: false`, and does not call vector sync.
- Cross-user material/folder access returns safe `404`.
- SQL move commits even if vector sync fails; material becomes `sync_state="sync_failed"`, `index_state="stale"`, response includes `VECTOR_SYNC_FAILED` and `retryable: true`.
- `MaterialVisualAsset.folder_id` follows material folder changes.
- Folder delete moves materials to uncategorized and marks ready material projections stale or pending.
- RAG fallback search filters by live SQL folder state, not stale vector metadata.

- [ ] **Step 2: Verify move/scope tests**

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong\backend"
python -m pytest tests\test_material_move_scope.py -v
Pop-Location
```

Expected: PASS.

- [ ] **Step 3: Commit**

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong"
git add backend/routes/materials.py backend/routes/folders.py backend/services/rag_service.py backend/services/vector_store_service.py backend/tests/test_material_move_scope.py
git commit -m @'
feat: add material folder move flow

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
'@
Pop-Location
```

---

### Task 3: Observable reindex jobs and two-generation safety

**Files:**
- Create: `backend/tests/test_reindex_jobs.py`
- Modify: `backend/models/material.py`
- Modify: `backend/models/__init__.py`
- Modify: `backend/routes/materials.py`
- Modify: `backend/services/rag_service.py`
- Modify: `backend/services/schema_service.py`

- [ ] **Step 1: Execute detailed source plan task group**

Follow all tasks in:

```text
D:\学习资料\大数据综合实践\zonghexitong\docs\superpowers\plans\2026-06-09-03-reindex-job-observability.md
```

Required behaviors:

- `ReindexJob.to_dict()` returns `job_id`, `material_id`, `generation`, `status`, `phase`, timestamps, `progress`, errors, `retryable`, `poll_url`.
- `POST /api/materials/<id>/reindex` returns `202` and does not synchronously block the request.
- Duplicate queued/running reindex returns the active job with message `索引重建已在进行中`.
- `GET /api/materials/<id>/index-status` returns material state, latest job, `ask_ai_available`, and `ask_ai_uses_generation`.
- Previous active generation remains available while building generation is queued/running/failed.
- Successful worker switches active generation only after the new index succeeds.
- Failure preserves previous active generation and marks the job retryable.
- Interrupted queued/running jobs become `stale` on status read/startup reconciliation.

- [ ] **Step 2: Verify reindex tests**

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong\backend"
python -m pytest tests\test_reindex_jobs.py -v
Pop-Location
```

Expected: PASS.

- [ ] **Step 3: Commit**

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong"
git add backend/models/material.py backend/models/__init__.py backend/routes/materials.py backend/services/rag_service.py backend/services/schema_service.py backend/tests/test_reindex_jobs.py
git commit -m @'
feat: add observable material reindex jobs

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
'@
Pop-Location
```

---

### Task 4: Image asset error envelopes and backend regression

**Files:**
- Modify: `backend/routes/materials.py`
- Modify: `backend/tests/test_materials_api.py`

- [ ] **Step 1: Add tests for image missing states**

Add or keep tests asserting:

- Missing asset row returns `404` with `error.code == "IMAGE_ASSET_NOT_FOUND"`.
- Missing image file returns `404` with `error.code == "IMAGE_FILE_MISSING"`, marks asset `missing_file`, and is retryable.

- [ ] **Step 2: Implement image endpoint envelopes**

In `get_material_asset_image`, return the standard error envelope for missing row/file instead of a bare `{message}` payload.

- [ ] **Step 3: Verify material regressions**

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong\backend"
python -m pytest tests\test_materials_api.py tests\test_material_move_scope.py tests\test_reindex_jobs.py tests\test_api_contract_schema.py -v
Pop-Location
```

Expected: PASS.

- [ ] **Step 4: Commit**

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong"
git add backend/routes/materials.py backend/tests/test_materials_api.py
git commit -m @'
feat: return stable material asset errors

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
'@
Pop-Location
```

---

### Task 5: Full backend verification

**Files:** all backend files touched by this plan.

- [ ] **Step 1: Run full backend test suite**

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong\backend"
python -m pytest tests -v
Pop-Location
```

Expected: PASS.

- [ ] **Step 2: Confirm no superseded combined plan was executed**

Review diff and verify changes are aligned with split source plans, not duplicated from the old combined plan:

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong"
git diff -- backend
Pop-Location
```

Expected: no duplicate `ReindexJob` definitions, no duplicate move routes, no duplicate scope helpers.

## Final acceptance

- [ ] Standard JSON errors exist and are used by new material endpoints.
- [ ] Scope service supports `uncategorized` with public `folder_id: null`.
- [ ] Material schema has index/sync/generation fields and idempotent compatibility migration.
- [ ] Material move updates SQL and visual rows; vector sync failure is visible but does not undo SQL classification.
- [ ] RAG fallback retrieval uses live SQL folder state.
- [ ] Reindex start/status contract is observable and generation-safe.
- [ ] Missing image assets return stable error codes.
- [ ] `python -m pytest tests -v` passes before frontend work starts.
