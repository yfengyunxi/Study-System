# Materials Move and Reindex Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the materials library reliable for the first learning step: classify uncategorized materials, move materials between folders, keep folder-scoped retrieval consistent, and expose observable reindex jobs.

**Architecture:** Add focused backend state to `Material` and `ReindexJob`, expose `PATCH /api/materials/:id/folder`, `POST /api/materials/:id/reindex`, and `GET /api/materials/:id/index-status`, then update Materials card/table UX to consume those contracts. Reindex uses persisted job rows with in-process execution and the two-generation rule so the previous ready generation stays available until a new generation succeeds.

**Tech Stack:** Flask, JWT, SQLAlchemy, pytest, Vue 3, Element Plus, Vite, Chroma-backed RAG services.

---

## Scope and dependencies

**User-flow position:** User enters the materials library, filters to uncategorized, classifies/moves one material, then optionally starts or watches reindex before asking AI in the selected folder.

**Depends on:** `D:\学习资料\大数据综合实践\zonghexitong\docs\superpowers\plans\2026-06-09-01-app-shell-visual-foundation.md` for shared error handling and visual tokens.

**Independently testable value:** After this plan, backend tests prove material move semantics, idempotent reindex status, stale generation behavior, and image error codes. Frontend build succeeds and manual checks prove card/table move controls, row loading, table overflow, reindex polling, and image placeholders work without implementing persistent chat or dashboard focus sessions.

## File structure

- Modify: `D:\学习资料\大数据综合实践\zonghexitong\backend\models\material.py`
  - Add `index_state`, `sync_state`, generation fields, and `ReindexJob` model.
- Modify: `D:\学习资料\大数据综合实践\zonghexitong\backend\services\schema_service.py`
  - Add non-destructive compatibility columns/tables for existing databases.
- Modify: `D:\学习资料\大数据综合实践\zonghexitong\backend\services\rag_service.py`
  - Add folder metadata sync and SQL-verified retrieval behavior for folder moves.
- Modify: `D:\学习资料\大数据综合实践\zonghexitong\backend\routes\materials.py`
  - Add move endpoint, 202 reindex job endpoint, status endpoint, JSON error envelopes, and image asset error codes.
- Modify: `D:\学习资料\大数据综合实践\zonghexitong\backend\routes\folders.py`
  - Keep folder delete/rename SQL truth and mark moved materials stale/sync-pending when needed.
- Modify: `D:\学习资料\大数据综合实践\zonghexitong\backend\tests\conftest.py`
  - Update fixtures with new fields and reindex job factory if needed.
- Modify: `D:\学习资料\大数据综合实践\zonghexitong\backend\tests\test_materials_api.py`
  - Add backend tests for move, reindex, image errors, and stale generation.
- Modify: `D:\学习资料\大数据综合实践\zonghexitong\frontend\src\api\modules.js`
  - Add `moveFolder` and `indexStatus` material API methods.
- Modify: `D:\学习资料\大数据综合实践\zonghexitong\frontend\src\components\study\MaterialCard.vue`
  - Add classify/move action and index state presentation.
- Modify: `D:\学习资料\大数据综合实践\zonghexitong\frontend\src\components\study\VisualAssetGrid.vue`
  - Convert failed image blobs into accessible placeholders.
- Modify: `D:\学习资料\大数据综合实践\zonghexitong\frontend\src\views\Materials.vue`
  - Add move dialog, table main-action + more-menu layout, row loading, folder counts refresh, reindex polling cleanup.
- Modify: `D:\学习资料\大数据综合实践\zonghexitong\frontend\src\views\MaterialDetail.vue`
  - Add reindex status display and image placeholder behavior if detail page loads assets directly.
- Modify: `D:\学习资料\大数据综合实践\zonghexitong\frontend\src\styles.css`
  - Add table/action/menu/status styles for the materials flow only.

## Tasks

### Task 1: Add backend model fields and reindex job schema

**Files:**
- Modify: `D:\学习资料\大数据综合实践\zonghexitong\backend\models\material.py`
- Modify: `D:\学习资料\大数据综合实践\zonghexitong\backend\services\schema_service.py`
- Modify: `D:\学习资料\大数据综合实践\zonghexitong\backend\tests\test_materials_api.py`

- [ ] **Step 1: Write failing schema test**

Append this test to `test_materials_api.py`:

```python
def test_material_schema_includes_phase_a_index_fields(app):
    from sqlalchemy import inspect

    inspector = inspect(db.engine)
    material_columns = {column["name"] for column in inspector.get_columns("material")}
    assert "index_state" in material_columns
    assert "sync_state" in material_columns
    assert "active_index_generation" in material_columns
    assert "building_index_generation" in material_columns
    assert inspector.has_table("reindex_job")
```

- [ ] **Step 2: Run the failing test**

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong\backend"
python -m pytest tests\test_materials_api.py::test_material_schema_includes_phase_a_index_fields -v
Pop-Location
```

Expected: FAIL because the new columns/table do not exist.

- [ ] **Step 3: Add model fields**

In `Material`, add these fields after `status`:

```python
    index_state = db.Column(db.String(20), default="not_indexed", nullable=False)
    sync_state = db.Column(db.String(20), default="synced", nullable=False)
    active_index_generation = db.Column(db.Integer, default=0, nullable=False)
    building_index_generation = db.Column(db.Integer, nullable=True)
```

Add this model after `MaterialVisualAsset`:

```python
class ReindexJob(db.Model):
    __tablename__ = "reindex_job"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    material_id = db.Column(db.Integer, db.ForeignKey("material.id"), nullable=False, index=True)
    generation = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default="queued", nullable=False, index=True)
    phase = db.Column(db.String(50), default="queued", nullable=False)
    chunks_indexed = db.Column(db.Integer, default=0, nullable=False)
    visual_assets_indexed = db.Column(db.Integer, default=0, nullable=False)
    visual_assets_failed = db.Column(db.Integer, default=0, nullable=False)
    last_error = db.Column(db.Text, nullable=True)
    error_code = db.Column(db.String(50), nullable=True)
    retryable = db.Column(db.Boolean, default=False, nullable=False)
    request_id = db.Column(db.String(120), nullable=True, index=True)
    started_at = db.Column(db.DateTime, nullable=True)
    finished_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow, nullable=True)

    material = db.relationship("Material", backref=db.backref("reindex_jobs", lazy=True, order_by="ReindexJob.created_at.desc()"))

    def to_dict(self):
        return {
            "job_id": self.id,
            "material_id": self.material_id,
            "generation": self.generation,
            "status": self.status,
            "phase": self.phase,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "progress": {
                "chunks_indexed": self.chunks_indexed,
                "visual_assets_indexed": self.visual_assets_indexed,
                "visual_assets_failed": self.visual_assets_failed,
            },
            "last_error": self.last_error,
            "error_code": self.error_code,
            "retryable": self.retryable,
            "poll_url": f"/api/materials/{self.material_id}/index-status",
        }
```

- [ ] **Step 4: Include new fields in `Material.to_dict`**

Add these keys to the data dict:

```python
            "index_state": self.index_state,
            "sync_state": self.sync_state,
            "active_index_generation": self.active_index_generation,
            "building_index_generation": self.building_index_generation,
```

- [ ] **Step 5: Update schema compatibility**

In `schema_service.py`, add statements for missing columns:

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

After executing statements, add backfill:

```python
        if "index_state" not in columns:
            db.session.execute(text("UPDATE material SET index_state = CASE WHEN status = 'ready' THEN 'ready' WHEN status = 'processing' THEN 'running' WHEN status = 'failed' THEN 'failed' ELSE 'not_indexed' END WHERE index_state IS NULL OR index_state = 'not_indexed'"))
        if "sync_state" not in columns:
            db.session.execute(text("UPDATE material SET sync_state = 'synced' WHERE sync_state IS NULL"))
```

`db.create_all()` already creates `reindex_job` in tests and fresh dev databases.

- [ ] **Step 6: Run schema test**

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong\backend"
python -m pytest tests\test_materials_api.py::test_material_schema_includes_phase_a_index_fields -v
Pop-Location
```

Expected: PASS.

### Task 2: Add material move endpoint and metadata sync

**Files:**
- Modify: `D:\学习资料\大数据综合实践\zonghexitong\backend\routes\materials.py`
- Modify: `D:\学习资料\大数据综合实践\zonghexitong\backend\services\rag_service.py`
- Modify: `D:\学习资料\大数据综合实践\zonghexitong\backend\tests\test_materials_api.py`

- [ ] **Step 1: Write failing move tests**

Append these tests:

```python
def test_move_uncategorized_material_to_folder(client, auth_headers, make_folder, make_material):
    headers, user = auth_headers()
    target = make_folder(user, name="数据仓库")
    material = make_material(user, folder=None, title="未分类讲义")

    response = client.patch(f"/api/materials/{material.id}/folder", headers=headers, json={"folder_id": target.id})

    assert response.status_code == 200
    data = response.get_json()
    assert data["changed"] is True
    assert data["sync_state"] == "synced"
    assert data["material"]["folder_id"] == target.id
    assert data["material"]["folder_name"] == "数据仓库"
    assert {item["folder_id"] for item in data["folder_counts"]} == {target.id, None}


def test_move_material_back_to_uncategorized(client, auth_headers, make_folder, make_material):
    headers, user = auth_headers()
    folder = make_folder(user)
    material = make_material(user, folder=folder)

    response = client.patch(f"/api/materials/{material.id}/folder", headers=headers, json={"folder_id": None})

    assert response.status_code == 200
    data = response.get_json()
    assert data["changed"] is True
    assert data["material"]["folder_id"] is None
    assert data["material"]["folder_name"] == ""


def test_move_material_same_target_is_noop(client, auth_headers, make_folder, make_material):
    headers, user = auth_headers()
    folder = make_folder(user)
    material = make_material(user, folder=folder)

    response = client.patch(f"/api/materials/{material.id}/folder", headers=headers, json={"folder_id": folder.id})

    assert response.status_code == 200
    data = response.get_json()
    assert data["changed"] is False
    assert data["sync_state"] == "synced"


def test_move_material_rejects_cross_user_folder(client, auth_headers, make_user, make_folder, make_material):
    headers, user = auth_headers()
    other = make_user("other-owner")
    other_folder = make_folder(other, name="别人")
    material = make_material(user)

    response = client.patch(f"/api/materials/{material.id}/folder", headers=headers, json={"folder_id": other_folder.id})

    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "NOT_FOUND"
```

- [ ] **Step 2: Run failing move tests**

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong\backend"
python -m pytest tests\test_materials_api.py::test_move_uncategorized_material_to_folder tests\test_materials_api.py::test_move_material_back_to_uncategorized tests\test_materials_api.py::test_move_material_same_target_is_noop tests\test_materials_api.py::test_move_material_rejects_cross_user_folder -v
Pop-Location
```

Expected: FAIL because endpoint does not exist.

- [ ] **Step 3: Add JSON error helper in `routes/materials.py`**

Add near constants:

```python
def api_error(code, message, status=400, retryable=False, details=None, field_errors=None):
    return jsonify({
        "message": message,
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
            "field_errors": field_errors or {},
            "retryable": retryable,
            "request_id": (request.get_json(silent=True) or {}).get("request_id", "") if request.method != "GET" else "",
        },
    }), status
```

- [ ] **Step 4: Add metadata sync method in `RAGService`**

Add this method:

```python
    def sync_material_folder_metadata(self, material):
        folder_id_value = material.folder_id or 0
        folder_name_value = material.folder.name if material.folder else ""
        updated = {
            "folder_id": folder_id_value,
            "folder_name": folder_name_value,
            "title": material.title,
        }
        try:
            self.vector_store.update_metadata(
                where={"$and": [{"user_id": material.user_id}, {"material_id": material.id}]},
                metadata=updated,
            )
        except AttributeError:
            current_app.logger.info("Vector store metadata update is not available; material %s will rely on SQL fallback", material.id)
        except Exception:
            current_app.logger.warning("Failed to sync text vector folder metadata for material %s", material.id, exc_info=True)
            raise
        try:
            self.visual_store.update_metadata(
                where={"$and": [{"user_id": material.user_id}, {"material_id": material.id}]},
                metadata=updated,
            )
        except AttributeError:
            current_app.logger.info("Visual vector metadata update is not available; material %s will rely on SQL fallback", material.id)
        except Exception:
            current_app.logger.warning("Failed to sync visual vector folder metadata for material %s", material.id, exc_info=True)
            raise
```

If `VectorStoreService` does not have `update_metadata`, add a method there that queries matching ids and updates metadatas using the underlying collection API. If Chroma update is awkward, keep this method as a best-effort hook and rely on SQL filtering in `_fallback_search`; failed sync must mark the material stale.

- [ ] **Step 5: Add move endpoint**

Add before `reindex_material`:

```python
@materials_bp.patch("/<int:material_id>/folder")
@jwt_required()
def move_material_folder(material_id):
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}
    material = Material.query.filter_by(id=material_id, user_id=user_id).first()
    if not material:
        return api_error("MATERIAL_NOT_FOUND", "资料不存在", 404)
    if material.status == "deleted":
        return api_error("CONFLICT", "资料已删除，不能移动", 409)

    if "folder_id" not in data:
        return api_error("VALIDATION_ERROR", "folder_id 字段不能为空；未分类请传 null", 400, field_errors={"folder_id": "required"})
    target_folder_id = data.get("folder_id")
    if target_folder_id is not None:
        try:
            target_folder_id = int(target_folder_id)
        except (TypeError, ValueError):
            return api_error("VALIDATION_ERROR", "folder_id 必须是数字或 null", 400, field_errors={"folder_id": "invalid"})
        folder = MaterialFolder.query.filter_by(id=target_folder_id, user_id=user_id).first()
        if not folder:
            return api_error("NOT_FOUND", "文件夹不存在", 404)

    changed = material.folder_id != target_folder_id
    if not changed:
        return jsonify({
            "message": "资料已在目标文件夹",
            "changed": False,
            "sync_state": "synced",
            "material": material.to_dict(),
            "folder_counts": _folder_counts(user_id, [target_folder_id, None]),
        })

    material.folder_id = target_folder_id
    material.sync_state = "synced"
    for asset in material.visual_assets:
        asset.folder_id = target_folder_id
    db.session.flush()

    try:
        RAGService().sync_material_folder_metadata(material)
    except Exception:
        material.sync_state = "sync_failed"
        material.index_state = "stale"
        db.session.commit()
        return jsonify({
            "message": "资料已移动，但索引同步失败，可重建索引修复检索范围",
            "changed": True,
            "sync_state": "sync_failed",
            "error_code": "VECTOR_SYNC_FAILED",
            "retryable": True,
            "material": material.to_dict(),
            "folder_counts": _folder_counts(user_id, [target_folder_id, None]),
        })

    db.session.commit()
    return jsonify({
        "message": "资料已移动到文件夹" if target_folder_id else "资料已移动到未分类",
        "changed": True,
        "sync_state": "synced",
        "material": material.to_dict(),
        "folder_counts": _folder_counts(user_id, [target_folder_id, None]),
    })
```

Add helper:

```python
def _folder_counts(user_id, folder_ids=None):
    ids = []
    for folder_id in folder_ids or []:
        if folder_id not in ids:
            ids.append(folder_id)
    if None not in ids:
        ids.append(None)
    return [
        {
            "folder_id": folder_id,
            "material_count": Material.query.filter_by(user_id=user_id, folder_id=folder_id).count(),
        }
        for folder_id in ids
    ]
```

- [ ] **Step 6: Run move tests**

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong\backend"
python -m pytest tests\test_materials_api.py::test_move_uncategorized_material_to_folder tests\test_materials_api.py::test_move_material_back_to_uncategorized tests\test_materials_api.py::test_move_material_same_target_is_noop tests\test_materials_api.py::test_move_material_rejects_cross_user_folder -v
Pop-Location
```

Expected: PASS.

### Task 3: Add observable reindex jobs

**Files:**
- Modify: `D:\学习资料\大数据综合实践\zonghexitong\backend\routes\materials.py`
- Modify: `D:\学习资料\大数据综合实践\zonghexitong\backend\tests\test_materials_api.py`

- [ ] **Step 1: Write failing reindex tests**

Append these tests:

```python
def test_reindex_returns_202_job_and_material_generation(client, auth_headers, make_material):
    headers, user = auth_headers()
    material = make_material(user, status="ready")
    material.index_state = "ready"
    material.active_index_generation = 4
    db.session.commit()

    response = client.post(f"/api/materials/{material.id}/reindex", headers=headers, json={"request_id": "reindex-test-1"})

    assert response.status_code == 202
    data = response.get_json()
    assert data["job"]["status"] in {"queued", "running", "succeeded"}
    assert data["job"]["generation"] == 5
    assert data["job"]["poll_url"] == f"/api/materials/{material.id}/index-status"
    assert data["material"]["active_index_generation"] == 4
    assert data["material"]["building_index_generation"] == 5


def test_reindex_status_marks_orphan_running_job_stale(client, auth_headers, make_material):
    from models.material import ReindexJob

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
```

- [ ] **Step 2: Run failing reindex tests**

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong\backend"
python -m pytest tests\test_materials_api.py::test_reindex_returns_202_job_and_material_generation tests\test_materials_api.py::test_reindex_status_marks_orphan_running_job_stale -v
Pop-Location
```

Expected: FAIL because job contract is not implemented.

- [ ] **Step 3: Import model and datetime helpers**

In `routes/materials.py`, update imports:

```python
from datetime import datetime
from threading import Thread
```

and model import:

```python
from models.material import Material, MaterialFolder, MaterialVisualAsset, ReindexJob
```

- [ ] **Step 4: Replace `reindex_material` with 202 job start**

```python
@materials_bp.post("/<int:material_id>/reindex")
@jwt_required()
def reindex_material(material_id):
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}
    material = Material.query.filter_by(id=material_id, user_id=user_id).first()
    if not material:
        return api_error("MATERIAL_NOT_FOUND", "资料不存在", 404)

    active_job = ReindexJob.query.filter(
        ReindexJob.user_id == user_id,
        ReindexJob.material_id == material_id,
        ReindexJob.status.in_(["queued", "running"]),
    ).order_by(ReindexJob.created_at.desc()).first()
    if active_job:
        return jsonify({"message": "索引重建已在进行中", "job": active_job.to_dict(), "material": material.to_dict()}), 202

    next_generation = (material.active_index_generation or 0) + 1
    material.status = "processing"
    material.index_state = "queued"
    material.building_index_generation = next_generation
    job = ReindexJob(
        user_id=user_id,
        material_id=material.id,
        generation=next_generation,
        status="queued",
        phase="queued",
        request_id=(data.get("request_id") or "")[:120],
    )
    db.session.add(job)
    db.session.commit()

    _start_reindex_background(current_app._get_current_object(), job.id)
    return jsonify({"message": "索引重建已开始", "job": job.to_dict(), "material": material.to_dict()}), 202
```

- [ ] **Step 5: Add status endpoint and stale-on-read behavior**

```python
@materials_bp.get("/<int:material_id>/index-status")
@jwt_required()
def material_index_status(material_id):
    user_id = int(get_jwt_identity())
    material = Material.query.filter_by(id=material_id, user_id=user_id).first()
    if not material:
        return api_error("MATERIAL_NOT_FOUND", "资料不存在", 404)
    job = ReindexJob.query.filter_by(user_id=user_id, material_id=material_id).order_by(ReindexJob.created_at.desc()).first()
    if job and job.status in {"queued", "running"}:
        job.status = "stale"
        job.phase = "stale_after_restart"
        job.retryable = True
        job.finished_at = datetime.utcnow()
        if material.active_index_generation:
            material.index_state = "stale"
        else:
            material.index_state = "failed"
        db.session.commit()
    ask_generation = material.active_index_generation or None
    return jsonify({
        "material_id": material.id,
        "status": material.status,
        "index_state": material.index_state,
        "active_index_generation": material.active_index_generation,
        "building_index_generation": material.building_index_generation,
        "job": job.to_dict() if job else None,
        "ask_ai_available": bool(ask_generation),
        "ask_ai_uses_generation": ask_generation,
    })
```

This endpoint intentionally marks queued/running as stale on read in tests and after process restart. If the same process has an active background registry, gate this behavior with a registry check; Phase A tests can simulate restart by clearing that registry.

- [ ] **Step 6: Add background executor**

```python
def _start_reindex_background(app, job_id):
    if app.config.get("TESTING"):
        return
    thread = Thread(target=_run_reindex_job, args=(app, job_id), daemon=True)
    thread.start()


def _run_reindex_job(app, job_id):
    with app.app_context():
        job = ReindexJob.query.get(job_id)
        if not job or job.status != "queued":
            return
        material = Material.query.filter_by(id=job.material_id, user_id=job.user_id).first()
        if not material:
            job.status = "stale"
            job.retryable = True
            job.finished_at = datetime.utcnow()
            db.session.commit()
            return
        job.status = "running"
        job.phase = "extracting"
        job.started_at = datetime.utcnow()
        material.index_state = "running"
        db.session.commit()
        try:
            _process_material(material, reindex=True, generation=job.generation, job=job)
            material.active_index_generation = job.generation
            material.building_index_generation = None
            material.index_state = "ready"
            material.status = "ready"
            job.status = "succeeded"
            job.phase = "completed"
            job.retryable = False
        except Exception as exc:
            current_app.logger.warning("Reindex job failed for material %s", material.id, exc_info=True)
            material.index_state = "failed" if not material.active_index_generation else "stale"
            material.status = "ready" if material.active_index_generation else "failed"
            job.status = "failed"
            job.phase = "failed"
            job.last_error = str(exc)
            job.error_code = "INDEX_FAILED"
            job.retryable = True
        finally:
            job.finished_at = datetime.utcnow()
            db.session.commit()
```

Update `_process_material` signature to accept optional `generation=None, job=None`; update job progress before commits:

```python
def _process_material(material, reindex=False, generation=None, job=None):
    ...
    if job:
        job.phase = "indexing_text"
        job.chunks_indexed = len(chunks)
    ...
    if job:
        job.phase = "indexing_visual"
        job.visual_assets_indexed = ready_visual_count
        job.visual_assets_failed = max(visual_count - ready_visual_count, 0)
```

- [ ] **Step 7: Run reindex tests**

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong\backend"
python -m pytest tests\test_materials_api.py::test_reindex_returns_202_job_and_material_generation tests\test_materials_api.py::test_reindex_status_marks_orphan_running_job_stale -v
Pop-Location
```

Expected: PASS.

### Task 4: Return stable image asset error envelopes

**Files:**
- Modify: `D:\学习资料\大数据综合实践\zonghexitong\backend\routes\materials.py`
- Modify: `D:\学习资料\大数据综合实践\zonghexitong\backend\tests\test_materials_api.py`

- [ ] **Step 1: Write failing image error tests**

Append:

```python
def test_image_asset_missing_row_returns_error_code(client, auth_headers):
    headers, _user = auth_headers()

    response = client.get("/api/materials/assets/999999/image", headers=headers)

    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "IMAGE_ASSET_NOT_FOUND"


def test_image_asset_missing_file_returns_error_code(client, auth_headers, make_material, make_visual_asset):
    headers, user = auth_headers()
    material = make_material(user)
    asset = make_visual_asset(material)

    response = client.get(f"/api/materials/assets/{asset.id}/image", headers=headers)

    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "IMAGE_FILE_MISSING"
```

- [ ] **Step 2: Run failing tests**

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong\backend"
python -m pytest tests\test_materials_api.py::test_image_asset_missing_row_returns_error_code tests\test_materials_api.py::test_image_asset_missing_file_returns_error_code -v
Pop-Location
```

Expected: FAIL because current endpoint returns only `message`.

- [ ] **Step 3: Update image endpoint**

Replace missing branches in `get_material_asset_image`:

```python
    if not asset:
        return api_error("IMAGE_ASSET_NOT_FOUND", "图片资料不存在", 404)
    image_path = Path(asset.image_path)
    if not image_path.exists():
        asset.status = "missing_file"
        db.session.commit()
        return api_error("IMAGE_FILE_MISSING", "图片文件不存在", 404, retryable=True)
```

- [ ] **Step 4: Run tests**

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong\backend"
python -m pytest tests\test_materials_api.py::test_image_asset_missing_row_returns_error_code tests\test_materials_api.py::test_image_asset_missing_file_returns_error_code -v
Pop-Location
```

Expected: PASS.

### Task 5: Update frontend material API methods

**Files:**
- Modify: `D:\学习资料\大数据综合实践\zonghexitong\frontend\src\api\modules.js`

- [ ] **Step 1: Add API methods**

Replace `materialApi` with:

```js
export const materialApi = {
  list: (params = {}) => http.get('/materials', { params }),
  detail: (id) => http.get(`/materials/${id}`),
  assets: (id) => http.get(`/materials/${id}/assets`),
  assetImage: (assetId) => http.get(`/materials/assets/${assetId}/image`, { responseType: 'blob' }),
  upload: (formData) => http.post('/materials/upload', formData),
  moveFolder: (id, data) => http.patch(`/materials/${id}/folder`, data),
  reindex: (id, data = {}) => http.post(`/materials/${id}/reindex`, data),
  indexStatus: (id) => http.get(`/materials/${id}/index-status`),
  remove: (id) => http.delete(`/materials/${id}`)
}
```

- [ ] **Step 2: Build**

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong\frontend"
npm run build
Pop-Location
```

Expected: PASS.

### Task 6: Add material card move and index status UI

**Files:**
- Modify: `D:\学习资料\大数据综合实践\zonghexitong\frontend\src\components\study\MaterialCard.vue`

- [ ] **Step 1: Update template action block**

Replace `material-card-actions` block with:

```vue
<div class="material-index-row" aria-live="polite">
  <el-tag :type="indexTagType">{{ indexLabel }}</el-tag>
  <span v-if="material.sync_state === 'sync_failed'" class="muted">索引同步失败，可重建修复</span>
</div>
<div class="material-card-actions">
  <el-button @click="$emit('view', material)">查看详情</el-button>
  <el-button type="primary" :disabled="material.status !== 'ready' && !material.active_index_generation" @click="$emit('ask', material)">
    {{ (material.status === 'ready' || material.active_index_generation) ? '向 AI 提问' : '暂不可问答' }}
  </el-button>
  <el-dropdown trigger="click" @command="(command) => $emit(command, material)">
    <el-button :aria-label="`${material.title} 更多操作`">更多</el-button>
    <template #dropdown>
      <el-dropdown-menu>
        <el-dropdown-item command="move">{{ material.folder_id ? '移动到文件夹' : '归类到文件夹' }}</el-dropdown-item>
        <el-dropdown-item command="reindex">重建索引</el-dropdown-item>
        <el-dropdown-item command="remove">删除</el-dropdown-item>
      </el-dropdown-menu>
    </template>
  </el-dropdown>
</div>
```

- [ ] **Step 2: Update script**

Replace `defineEmits` and add computed helpers:

```js
defineEmits(['view', 'ask', 'move', 'reindex', 'remove'])

const indexLabel = computed(() => {
  const state = props.material.index_state || (props.material.status === 'ready' ? 'ready' : 'not_indexed')
  const labels = {
    not_indexed: '未索引',
    queued: '索引排队中',
    running: '索引重建中',
    ready: '索引可用',
    failed: '索引失败',
    stale: '索引需刷新'
  }
  return labels[state] || state
})

const indexTagType = computed(() => {
  const state = props.material.index_state || 'not_indexed'
  if (state === 'ready') return 'success'
  if (state === 'queued' || state === 'running') return 'warning'
  if (state === 'failed' || props.material.sync_state === 'sync_failed') return 'danger'
  return 'info'
})
```

- [ ] **Step 3: Build**

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong\frontend"
npm run build
Pop-Location
```

Expected: PASS.

### Task 7: Add Materials move dialog, table actions, and reindex polling

**Files:**
- Modify: `D:\学习资料\大数据综合实践\zonghexitong\frontend\src\views\Materials.vue`
- Modify: `D:\学习资料\大数据综合实践\zonghexitong\frontend\src\styles.css`

- [ ] **Step 1: Update `MaterialCard` bindings**

Add the move event:

```vue
<MaterialCard
  v-for="material in visibleMaterials"
  :key="material.id"
  :material="material"
  @view="goDetail"
  @ask="goAsk"
  @move="openMoveDialog"
  @reindex="reindex"
  @remove="removeMaterial"
/>
```

- [ ] **Step 2: Replace table action column**

Replace the current operation column with:

```vue
<el-table-column label="操作" width="190" fixed="right">
  <template #default="{ row }">
    <div class="table-actions">
      <el-button :loading="rowLoading[row.id]" :icon="View" @click="goDetail(row)">查看</el-button>
      <el-dropdown trigger="click" @command="(command) => handleTableCommand(command, row)">
        <el-button :aria-label="`${row.title} 更多操作`">更多</el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="ask" :disabled="row.status !== 'ready' && !row.active_index_generation">向 AI 提问</el-dropdown-item>
            <el-dropdown-item command="move">{{ row.folder_id ? '移动到文件夹' : '归类到文件夹' }}</el-dropdown-item>
            <el-dropdown-item command="reindex">重建索引</el-dropdown-item>
            <el-dropdown-item command="remove">删除</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </template>
</el-table-column>
```

- [ ] **Step 3: Add move dialog after folder dialog**

```vue
<el-dialog v-model="moveDialog" :title="moveTarget?.folder_id ? '移动到文件夹' : '归类到文件夹'" width="440px">
  <p class="muted">当前资料：{{ moveTarget?.title }}</p>
  <el-form label-position="top">
    <el-form-item label="目标文件夹">
      <el-select v-model="moveFolderId" class="full-width" placeholder="选择目标文件夹">
        <el-option label="未分类" :value="null" />
        <el-option v-for="folder in folders" :key="folder.id" :label="folder.name" :value="folder.id" />
      </el-select>
    </el-form-item>
  </el-form>
  <template #footer>
    <el-button @click="moveDialog = false">取消</el-button>
    <el-button type="primary" :loading="moving" :disabled="moveFolderId === moveTarget?.folder_id" @click="moveMaterial">确认移动</el-button>
  </template>
</el-dialog>
```

- [ ] **Step 4: Update imports and state**

Change Vue import:

```js
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
```

Add state near other refs:

```js
const moveDialog = ref(false)
const moveTarget = ref(null)
const moveFolderId = ref(null)
const moving = ref(false)
const rowLoading = reactive({})
const pollTimers = new Map()
```

- [ ] **Step 5: Add table command and move functions**

```js
function handleTableCommand(command, row) {
  if (command === 'ask') goAsk(row)
  if (command === 'move') openMoveDialog(row)
  if (command === 'reindex') reindex(row)
  if (command === 'remove') removeMaterial(row)
}

function openMoveDialog(material) {
  moveTarget.value = material
  moveFolderId.value = material.folder_id ?? null
  moveDialog.value = true
}

async function moveMaterial() {
  if (!moveTarget.value) return
  moving.value = true
  rowLoading[moveTarget.value.id] = true
  try {
    const result = await materialApi.moveFolder(moveTarget.value.id, {
      folder_id: moveFolderId.value,
      request_id: `move-${moveTarget.value.id}-${Date.now()}`
    })
    const updated = result.material
    allMaterials.value = allMaterials.value.map((item) => item.id === updated.id ? { ...item, ...updated } : item)
    await loadFolders()
    if (result.sync_state === 'sync_failed') {
      ElMessage.warning(result.message)
    } else {
      ElMessage.success(result.message || '资料已移动')
    }
    moveDialog.value = false
  } finally {
    moving.value = false
    rowLoading[moveTarget.value?.id] = false
  }
}
```

- [ ] **Step 6: Replace `reindex` with polling version**

```js
async function reindex(material) {
  rowLoading[material.id] = true
  try {
    const result = await materialApi.reindex(material.id, { request_id: `reindex-${material.id}-${Date.now()}` })
    mergeMaterial(result.material)
    ElMessage.success(result.message || '索引重建已开始')
    startIndexPolling(material.id)
  } finally {
    rowLoading[material.id] = false
  }
}

function mergeMaterial(material) {
  if (!material) return
  allMaterials.value = allMaterials.value.map((item) => item.id === material.id ? { ...item, ...material } : item)
}

function startIndexPolling(materialId) {
  stopIndexPolling(materialId)
  const startedAt = Date.now()
  const poll = async () => {
    try {
      const status = await materialApi.indexStatus(materialId)
      mergeMaterial({
        id: materialId,
        status: status.status,
        index_state: status.index_state,
        active_index_generation: status.active_index_generation,
        building_index_generation: status.building_index_generation
      })
      if (!status.job || ['succeeded', 'failed', 'cancelled', 'stale'].includes(status.job.status)) {
        stopIndexPolling(materialId)
        if (status.job?.status === 'succeeded') ElMessage.success('索引重建完成')
        if (status.job?.status === 'failed') ElMessage.error(status.job.last_error || '索引重建失败')
        if (status.job?.status === 'stale') ElMessage.warning('索引任务已失效，可重新触发')
        return
      }
      const elapsed = Date.now() - startedAt
      if (elapsed > 5 * 60 * 1000) {
        stopIndexPolling(materialId)
        ElMessage.warning('索引仍在处理中，可稍后刷新')
        return
      }
      const delay = elapsed < 60 * 1000 ? 2000 : 5000
      pollTimers.set(materialId, window.setTimeout(poll, delay))
    } catch (error) {
      stopIndexPolling(materialId)
    }
  }
  pollTimers.set(materialId, window.setTimeout(poll, 2000))
}

function stopIndexPolling(materialId) {
  const timer = pollTimers.get(materialId)
  if (timer) window.clearTimeout(timer)
  pollTimers.delete(materialId)
}

onBeforeUnmount(() => {
  for (const timer of pollTimers.values()) window.clearTimeout(timer)
  pollTimers.clear()
})
```

- [ ] **Step 7: Add styles**

```css
.table-actions {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  white-space: nowrap;
}

.material-index-row {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-top: var(--space-3);
  flex-wrap: wrap;
}
```

- [ ] **Step 8: Build**

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong\frontend"
npm run build
Pop-Location
```

Expected: PASS.

### Task 8: Add image fallback placeholder in asset grids

**Files:**
- Modify: `D:\学习资料\大数据综合实践\zonghexitong\frontend\src\components\study\VisualAssetGrid.vue`

- [ ] **Step 1: Ensure failed blob loads display accessible placeholder**

If the component currently renders `<img>` directly, add a per-asset error map and render this placeholder when the blob request fails:

```vue
<div v-if="failedAssets[asset.id]" class="asset-placeholder" role="img" :aria-label="`${asset.caption || asset.material_title || '图片资料'} 暂不可用`">
  <strong>图片暂不可用</strong>
  <p>{{ asset.caption || '该图片文件缺失或没有访问权限。' }}</p>
  <small>资料 {{ asset.material_id }} · 可尝试重建索引或重新上传资料</small>
</div>
<img v-else-if="imageUrls[asset.id]" :src="imageUrls[asset.id]" :alt="asset.caption || '视觉资料'" />
```

Use this loader shape:

```js
const failedAssets = ref({})

async function loadAssetImage(asset) {
  try {
    const blob = await materialApi.assetImage(asset.id)
    imageUrls.value[asset.id] = URL.createObjectURL(blob)
  } catch (error) {
    failedAssets.value[asset.id] = error.apiError?.code || 'IMAGE_LOAD_FAILED'
  }
}
```

- [ ] **Step 2: Build**

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong\frontend"
npm run build
Pop-Location
```

Expected: PASS.

### Task 9: Full backend and frontend verification

**Files:**
- All files in this plan.

- [ ] **Step 1: Run material API tests**

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong\backend"
python -m pytest tests\test_materials_api.py -v
Pop-Location
```

Expected: PASS.

- [ ] **Step 2: Run all backend tests**

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong\backend"
python -m pytest tests -v
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

- [ ] **Step 4: Manual acceptance checks**

1. Open `/materials`.
2. Select `未分类`.
3. Move one material to an existing folder; expected: row/card shows loading, material disappears from `未分类`, folder counts update.
4. Move a classified material back to `未分类`; expected: `folder_id: null` behavior in the API and visible `未分类` label.
5. Switch to table mode at 390px and 1366px; expected: table scrolls only inside `.table-wrap`, operation column uses `查看 + 更多`, no body horizontal scroll.
6. Trigger `重建索引`; expected: immediate queued/running UI, disabled/loading action while request is active, polling stops on terminal state or after 5 minutes.
7. Force an image asset 404; expected: accessible placeholder with caption/material/recovery copy and no infinite retry.

### Task 10: Commit material flow changes

**Files:**
- Modify: all backend and frontend files listed in this plan.

- [ ] **Step 1: Review focused diff**

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong"
git diff -- "backend/models/material.py" "backend/routes/materials.py" "backend/routes/folders.py" "backend/services/rag_service.py" "backend/services/schema_service.py" "backend/tests" "frontend/src/api/modules.js" "frontend/src/components/study/MaterialCard.vue" "frontend/src/components/study/VisualAssetGrid.vue" "frontend/src/views/Materials.vue" "frontend/src/views/MaterialDetail.vue" "frontend/src/styles.css"
Pop-Location
```

Expected: diff contains no unrelated chat/dashboard implementation.

- [ ] **Step 2: Commit**

```powershell
git add "D:\学习资料\大数据综合实践\zonghexitong\backend\models\material.py" "D:\学习资料\大数据综合实践\zonghexitong\backend\routes\materials.py" "D:\学习资料\大数据综合实践\zonghexitong\backend\routes\folders.py" "D:\学习资料\大数据综合实践\zonghexitong\backend\services\rag_service.py" "D:\学习资料\大数据综合实践\zonghexitong\backend\services\schema_service.py" "D:\学习资料\大数据综合实践\zonghexitong\backend\tests" "D:\学习资料\大数据综合实践\zonghexitong\frontend\src\api\modules.js" "D:\学习资料\大数据综合实践\zonghexitong\frontend\src\components\study\MaterialCard.vue" "D:\学习资料\大数据综合实践\zonghexitong\frontend\src\components\study\VisualAssetGrid.vue" "D:\学习资料\大数据综合实践\zonghexitong\frontend\src\views\Materials.vue" "D:\学习资料\大数据综合实践\zonghexitong\frontend\src\views\MaterialDetail.vue" "D:\学习资料\大数据综合实践\zonghexitong\frontend\src\styles.css"
git commit -m @'
feat: repair materials move and reindex flow

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
'@
```

## Final verification for this plan

Run:

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong\backend"
python -m pytest tests -v
Pop-Location
Push-Location "D:\学习资料\大数据综合实践\zonghexitong\frontend"
npm run build
Pop-Location
```

Expected: all backend tests pass and frontend build passes. Manual acceptance covers material move, folder-scope consistency, reindex polling, table overflow, and image placeholders.
