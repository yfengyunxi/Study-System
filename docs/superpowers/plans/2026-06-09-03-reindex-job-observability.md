# Reindex Job Observability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace opaque synchronous material reindexing with a persisted job/status contract and generation-safe index rebuilds.

**Architecture:** Add a `ReindexJob` table and status API around the existing material processing pipeline. Start Phase A with an in-process executor, reconcile interrupted jobs as `stale`, and never replace `active_index_generation` until the new generation succeeds.

**Tech Stack:** Flask 3, Flask-SQLAlchemy, Flask-JWT-Extended, pytest, Python threads, existing RAG/vector services.

---

## Backend dependency order

Depends on:

1. `D:\学习资料\大数据综合实践\zonghexitong\docs\superpowers\plans\2026-06-09-01-backend-contract-schema-foundation.md`
2. `D:\学习资料\大数据综合实践\zonghexitong\docs\superpowers\plans\2026-06-09-02-material-move-rag-scope-consistency.md`

This plan is a backend prerequisite for stable AI chat because chat needs to know whether the previous ready generation remains queryable during rebuild.

## Independent verification

Backend:

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong\backend"
python -m pytest tests/test_reindex_jobs.py -v
Pop-Location
```

Frontend build if polling UI is implemented in this plan:

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong\frontend"
npm run build
Pop-Location
```

## File structure and responsibilities

- Create: `backend/tests/test_reindex_jobs.py`  
  Tests job model serialization, `POST /api/materials/:id/reindex` returning 202, duplicate active job coalescing, `GET /api/materials/:id/index-status`, stale reconciliation, success generation switch, and failure preserving the old active generation.

- Modify: `backend/models/material.py`  
  Add `ReindexJob` with `queued/running/succeeded/failed/cancelled/stale`, phase, progress JSON, request id, timestamps, and retry fields.

- Modify: `backend/models/__init__.py`  
  Export `ReindexJob`.

- Modify: `backend/routes/materials.py`  
  Replace synchronous reindex response with 202 job response, add status endpoint, and run the rebuild in a background application-context worker.

- Modify: `backend/services/rag_service.py`  
  Add generation-aware text/visual index write helpers and cleanup helpers that delete old generations only after success.

- Modify: `backend/services/schema_service.py`  
  Ensure new tables/columns are created and interrupted active jobs are reconciled safely.

- Modify: `frontend/src/api/modules.js`, `frontend/src/views/Materials.vue`, `frontend/src/components/study/MaterialCard.vue`, `frontend/src/components/study/StatusBadge.vue`  
  Add `indexStatus`, job polling, loading/disabled states, and failed/stale retry presentation.

---

### Task 1: Add ReindexJob model

**Files:**
- Modify: `backend/models/material.py`
- Modify: `backend/models/__init__.py`
- Test: `backend/tests/test_reindex_jobs.py`

- [ ] **Step 1: Write model serialization test**

Create `backend/tests/test_reindex_jobs.py` with a test that inserts `ReindexJob(user_id, material_id, generation=2, status="queued", phase="queued", progress_json='{"chunks_indexed": 0}')` and asserts `to_dict()` returns `job_id`, `material_id`, `generation`, `status`, `phase`, `started_at`, `finished_at`, `progress`, `last_error`, `error_code`, `retryable`, and `poll_url: /api/materials/<id>/index-status`.

- [ ] **Step 2: Run the model test**

```powershell
python -m pytest tests/test_reindex_jobs.py::test_reindex_job_to_dict_includes_poll_contract -v
```

Expected: FAIL before the model exists.

- [ ] **Step 3: Implement the model**

Add `ReindexJob` to `backend/models/material.py` with these columns: `id`, `user_id`, `material_id`, `generation`, `status`, `phase`, `progress_json`, `last_error`, `error_code`, `retryable`, `request_id`, `started_at`, `finished_at`, `created_at`, `updated_at`. Add `to_dict()` with the response shape from the spec.

- [ ] **Step 4: Export the model**

Update `backend/models/__init__.py` so `ReindexJob` is imported and present in `__all__`.

- [ ] **Step 5: Run the model test again**

```powershell
python -m pytest tests/test_reindex_jobs.py::test_reindex_job_to_dict_includes_poll_contract -v
```

Expected: PASS.

---

### Task 2: Implement 202 reindex start and status endpoints

**Files:**
- Modify: `backend/routes/materials.py`
- Test: `backend/tests/test_reindex_jobs.py`

- [ ] **Step 1: Write endpoint tests**

Add tests that assert:

- first `POST /api/materials/<id>/reindex` returns HTTP 202 with `job.status == "queued"`, `material.index_state == "queued"`, and `building_index_generation == active_index_generation + 1`;
- duplicate `POST` while `queued` or `running` returns HTTP 202 with the same active job and message `索引重建已在进行中`;
- `GET /api/materials/<id>/index-status` returns `ask_ai_available: true` and `ask_ai_uses_generation` equal to the previous `active_index_generation` when a previous ready generation exists;
- cross-user material access returns 404 with `MATERIAL_NOT_FOUND`.

- [ ] **Step 2: Run endpoint tests**

```powershell
python -m pytest tests/test_reindex_jobs.py::test_reindex_start_returns_202_job tests/test_reindex_jobs.py::test_duplicate_reindex_returns_existing_active_job -v
```

Expected: FAIL before route changes.

- [ ] **Step 3: Implement route helpers**

In `backend/routes/materials.py`, add helpers to find active jobs, create the next generation, serialize status, and start a background worker. The start response must be exactly shaped like the spec: top-level `message`, `job`, and `material`.

- [ ] **Step 4: Implement endpoints**

Change `POST /api/materials/<id>/reindex` to return 202 and add `GET /api/materials/<id>/index-status`. Do not call `_process_material()` synchronously from the request handler.

- [ ] **Step 5: Run endpoint tests again**

```powershell
python -m pytest tests/test_reindex_jobs.py::test_reindex_start_returns_202_job tests/test_reindex_jobs.py::test_reindex_status_reports_previous_generation_available -v
```

Expected: PASS.

---

### Task 3: Implement generation-safe worker completion and failure

**Files:**
- Modify: `backend/routes/materials.py`
- Modify: `backend/services/rag_service.py`
- Test: `backend/tests/test_reindex_jobs.py`

- [ ] **Step 1: Write worker tests**

Add tests for:

- successful worker switches `active_index_generation` to the job generation, clears `building_index_generation`, sets `index_state="ready"`, and sets job `succeeded`;
- failed worker keeps previous `active_index_generation`, clears `building_index_generation`, sets `index_state="failed"` only when no previous generation exists and otherwise leaves AI available with previous generation, and sets job `failed` with `retryable=true`;
- deleting a material with active job marks the job `cancelled` or ignores late completion.

- [ ] **Step 2: Run worker tests**

```powershell
python -m pytest tests/test_reindex_jobs.py::test_reindex_success_switches_active_generation tests/test_reindex_jobs.py::test_reindex_failure_preserves_previous_ready_generation -v
```

Expected: FAIL before worker completion logic exists.

- [ ] **Step 3: Add generation metadata to RAG writes**

Update `RAGService.index_material()` and `RAGService.index_visual_assets()` so generated Chroma ids and metadata include `generation`. Add `delete_material_generation_vectors(user_id, material_id, generation)` and `delete_old_material_generations(user_id, material_id, keep_generation)` helpers.

- [ ] **Step 4: Add worker state transitions**

Implement `_run_reindex_job(app, job_id)` in `backend/routes/materials.py`: set `running`, update phase/progress, extract text/assets, write the building generation, commit success, then delete old vectors. On exception, set job `failed`, set `last_error`, `error_code="INDEX_FAILED"`, `retryable=True`, and preserve previous active generation.

- [ ] **Step 5: Run worker tests again**

```powershell
python -m pytest tests/test_reindex_jobs.py::test_reindex_success_switches_active_generation tests/test_reindex_jobs.py::test_reindex_failure_preserves_previous_ready_generation -v
```

Expected: PASS.

---

### Task 4: Reconcile stale jobs after restart

**Files:**
- Modify: `backend/routes/materials.py`
- Modify: `backend/services/schema_service.py`
- Test: `backend/tests/test_reindex_jobs.py`

- [ ] **Step 1: Write stale reconciliation test**

Add a test that creates a `running` job, calls `GET /api/materials/<id>/index-status` without an in-memory worker, and asserts the job becomes `stale`, `retryable=true`, material `index_state="stale"` only when no active ready generation exists, and previous generation remains available when present.

- [ ] **Step 2: Run stale test**

```powershell
python -m pytest tests/test_reindex_jobs.py::test_status_marks_interrupted_running_job_stale -v
```

Expected: FAIL before reconciliation exists.

- [ ] **Step 3: Implement stale reconciliation**

Add a helper in `routes/materials.py` that marks `queued/running` jobs stale when no worker is known for that job id. Call it from status reads. Also call a startup-safe reconciliation in `ensure_schema_compatibility(app)` after `db.create_all()`.

- [ ] **Step 4: Run stale test again**

```powershell
python -m pytest tests/test_reindex_jobs.py::test_status_marks_interrupted_running_job_stale -v
```

Expected: PASS.

---

### Task 5: Add frontend polling UI

**Files:**
- Modify: `frontend/src/api/modules.js`
- Modify: `frontend/src/views/Materials.vue`
- Modify: `frontend/src/components/study/MaterialCard.vue`
- Modify: `frontend/src/components/study/StatusBadge.vue`

- [ ] **Step 1: Add API methods**

Add:

```javascript
reindex: (id, data = {}) => http.post(`/materials/${id}/reindex`, data),
indexStatus: (id) => http.get(`/materials/${id}/index-status`)
```

- [ ] **Step 2: Update material cards/status**

Show `index_state` separately from coarse `status`. Disable repeated reindex while `index_state` is `queued` or `running`; keep ask AI enabled when backend status says `ask_ai_available` for previous generation.

- [ ] **Step 3: Add polling lifecycle**

In `Materials.vue`, after a 202 response, poll every 2 seconds for 60 seconds, then every 5 seconds until 5 minutes, then stop and show `仍在处理中，可稍后刷新`. Clean all timers in `onBeforeUnmount()`.

- [ ] **Step 4: Build frontend**

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong\frontend"
npm run build
Pop-Location
```

Expected: PASS.

---

### Task 6: Full verification and commit

- [ ] **Step 1: Run backend plan tests**

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong\backend"
python -m pytest tests/test_reindex_jobs.py -v
Pop-Location
```

Expected: PASS.

- [ ] **Step 2: Run material regression tests**

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong\backend"
python -m pytest tests/test_materials_api.py tests/test_material_move_scope.py -v
Pop-Location
```

Expected: PASS.

- [ ] **Step 3: Run frontend build**

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong\frontend"
npm run build
Pop-Location
```

Expected: PASS.

- [ ] **Step 4: Commit**

```powershell
git add backend/models/material.py backend/models/__init__.py backend/routes/materials.py backend/services/rag_service.py backend/services/schema_service.py backend/tests/test_reindex_jobs.py frontend/src/api/modules.js frontend/src/views/Materials.vue frontend/src/components/study/MaterialCard.vue frontend/src/components/study/StatusBadge.vue
git commit -m "feat: add observable material reindex jobs"
```

---

## Self-review checklist

- Spec coverage: covers 202 accepted, job/status payloads, duplicate coalescing, stale reconciliation, two-generation safety, and polling UI.
- Independent testability: backend job tests can run with mocked document/RAG functions; frontend build verifies polling code compiles.
- Intentional deferrals: production distributed queues and cross-process workers remain out of Phase A.
