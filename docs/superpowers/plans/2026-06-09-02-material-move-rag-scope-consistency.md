# Material Move and RAG Scope Consistency Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let users move a single material into a folder, into another folder, or back to uncategorized while keeping SQL, visual assets, vector metadata, and folder-scope retrieval consistent.

**Architecture:** Add the backend move endpoint first, then centralize RAG projection updates and live SQL validation before adding frontend entry points. SQL remains canonical; vector metadata is a projection that can be marked stale if synchronization fails.

**Tech Stack:** Flask 3, Flask-SQLAlchemy, Flask-JWT-Extended, pytest, existing `RAGService` and Chroma-backed `VectorStoreService`, Vue 3, Element Plus.

---

## Backend dependency order

Depends on `D:\学习资料\大数据综合实践\zonghexitong\docs\superpowers\plans\2026-06-09-01-backend-contract-schema-foundation.md` for `error_response`, `index_state`, and `sync_state`.

This plan should be implemented before reindex jobs and chat persistence because both need correct material folder state and scope filtering.

## Independent verification

Backend:

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong\backend"
python -m pytest tests/test_material_move_scope.py -v
Pop-Location
```

Frontend build after UI changes:

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong\frontend"
npm run build
Pop-Location
```

## File structure and responsibilities

- Create: `backend/tests/test_material_move_scope.py`  
  Drives move endpoint behavior, no-op moves, cross-user safety, sync failure partial success, folder delete reconciliation, and RAG scope validation.

- Modify: `backend/routes/materials.py`  
  Adds `PATCH /api/materials/:id/folder` and returns updated material plus folder counts.

- Modify: `backend/routes/folders.py`  
  Marks affected materials stale/sync-pending when a folder is deleted and materials move to uncategorized.

- Modify: `backend/services/rag_service.py`  
  Adds projection sync helpers and SQL-validated retrieval for folder/material/uncategorized scopes.

- Modify: `backend/services/vector_store_service.py`  
  Adds metadata update support by delete/re-upsert or collection-specific metadata update if available.

- Modify: `frontend/src/api/modules.js`  
  Adds `materialApi.moveFolder(id, data)`.

- Modify: `frontend/src/views/Materials.vue` and `frontend/src/components/study/MaterialCard.vue`  
  Adds card/table move actions and a folder target dialog.

---

### Task 1: Add backend material move contract

**Files:**
- Create: `backend/tests/test_material_move_scope.py`
- Modify: `backend/routes/materials.py`

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_material_move_scope.py`:

```python
from unittest.mock import patch

from extensions import db
from models.material import MaterialVisualAsset


def test_move_uncategorized_material_to_folder(client, auth_headers, make_folder, make_material, make_visual_asset):
    headers, user = auth_headers()
    target = make_folder(user, name="数据仓库")
    material = make_material(user, folder=None, title="未分类资料", status="ready")
    asset = make_visual_asset(material, status="ready")

    with patch("routes.materials.RAGService") as rag_cls:
        rag_cls.return_value.sync_material_folder_metadata.return_value = True
        response = client.patch(
            f"/api/materials/{material.id}/folder",
            headers=headers,
            json={"folder_id": target.id, "request_id": "move-1"},
        )

    assert response.status_code == 200
    data = response.get_json()
    assert data["changed"] is True
    assert data["sync_state"] == "synced"
    assert data["material"]["folder_id"] == target.id
    assert data["material"]["folder_name"] == "数据仓库"
    assert {item["folder_id"] for item in data["folder_counts"]} == {target.id, None}

    db.session.refresh(material)
    db.session.refresh(asset)
    assert material.folder_id == target.id
    assert material.sync_state == "synced"
    assert material.index_state == "ready"
    assert asset.folder_id == target.id
    rag_cls.return_value.sync_material_folder_metadata.assert_called_once_with(material)


def test_move_material_to_uncategorized(client, auth_headers, make_folder, make_material):
    headers, user = auth_headers()
    folder = make_folder(user)
    material = make_material(user, folder=folder, status="ready")

    with patch("routes.materials.RAGService") as rag_cls:
        rag_cls.return_value.sync_material_folder_metadata.return_value = True
        response = client.patch(
            f"/api/materials/{material.id}/folder",
            headers=headers,
            json={"folder_id": None, "request_id": "move-uncategorized"},
        )

    assert response.status_code == 200
    data = response.get_json()
    assert data["changed"] is True
    assert data["material"]["folder_id"] is None
    assert data["material"]["folder_name"] == ""


def test_move_material_same_target_is_noop(client, auth_headers, make_folder, make_material):
    headers, user = auth_headers()
    folder = make_folder(user)
    material = make_material(user, folder=folder, status="ready")

    with patch("routes.materials.RAGService") as rag_cls:
        response = client.patch(
            f"/api/materials/{material.id}/folder",
            headers=headers,
            json={"folder_id": folder.id, "request_id": "move-same"},
        )

    assert response.status_code == 200
    data = response.get_json()
    assert data["changed"] is False
    assert data["sync_state"] == "synced"
    rag_cls.return_value.sync_material_folder_metadata.assert_not_called()


def test_move_material_rejects_cross_user_folder(client, auth_headers, make_user, make_folder, make_material):
    headers, user = auth_headers()
    other = make_user("other-user")
    other_folder = make_folder(other, name="other-folder")
    material = make_material(user, status="ready")

    response = client.patch(
        f"/api/materials/{material.id}/folder",
        headers=headers,
        json={"folder_id": other_folder.id, "request_id": "move-cross-user"},
    )

    assert response.status_code == 404
    data = response.get_json()
    assert data["error"]["code"] == "NOT_FOUND"


def test_move_material_sync_failure_marks_stale_but_keeps_sql_change(client, auth_headers, make_folder, make_material):
    headers, user = auth_headers()
    folder = make_folder(user)
    material = make_material(user, status="ready")

    with patch("routes.materials.RAGService") as rag_cls:
        rag_cls.return_value.sync_material_folder_metadata.side_effect = RuntimeError("chroma unavailable")
        response = client.patch(
            f"/api/materials/{material.id}/folder",
            headers=headers,
            json={"folder_id": folder.id, "request_id": "move-sync-fail"},
        )

    assert response.status_code == 200
    data = response.get_json()
    assert data["changed"] is True
    assert data["sync_state"] == "sync_failed"
    assert data["error_code"] == "VECTOR_SYNC_FAILED"
    assert data["retryable"] is True
    assert data["material"]["folder_id"] == folder.id
    assert data["material"]["index_state"] == "stale"

    db.session.refresh(material)
    assert material.folder_id == folder.id
    assert material.sync_state == "sync_failed"
    assert material.index_state == "stale"
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
python -m pytest tests/test_material_move_scope.py -v
```

Expected: FAIL because `PATCH /api/materials/:id/folder` does not exist.

- [ ] **Step 3: Implement endpoint helper functions**

In `backend/routes/materials.py`, import the error helper:

```python
from services.error_service import error_response
```

Add these helpers before `_parse_bool_arg`:

```python
def _folder_counts(user_id, changed_folder_ids):
    counts = []
    folder_ids = [folder_id for folder_id in changed_folder_ids if folder_id is not None]
    for folder_id in folder_ids:
        counts.append(
            {
                "folder_id": folder_id,
                "material_count": Material.query.filter_by(user_id=user_id, folder_id=folder_id).count(),
            }
        )
    if None in changed_folder_ids:
        counts.append(
            {
                "folder_id": None,
                "material_count": Material.query.filter_by(user_id=user_id, folder_id=None).count(),
            }
        )
    return counts


def _parse_target_folder_id(data):
    if "folder_id" not in data or data.get("folder_id") is None:
        return None
    try:
        return int(data.get("folder_id"))
    except (TypeError, ValueError):
        raise ValueError("folder_id 必须是数字或 null")
```

- [ ] **Step 4: Implement the move endpoint**

Add this route in `backend/routes/materials.py` before `reindex_material`:

```python
@materials_bp.patch("/<int:material_id>/folder")
@jwt_required()
def move_material_folder(material_id):
    user_id = int(get_jwt_identity())
    material = Material.query.filter_by(id=material_id, user_id=user_id).first()
    if not material:
        return error_response("MATERIAL_NOT_FOUND", "资料不存在", status=404)
    if material.status == "deleted":
        return error_response("CONFLICT", "资料已删除，不能移动", status=409)

    data = request.get_json(silent=True) or {}
    try:
        target_folder_id = _parse_target_folder_id(data)
    except ValueError as exc:
        return error_response("VALIDATION_ERROR", str(exc), status=400)

    if target_folder_id is not None:
        folder = MaterialFolder.query.filter_by(id=target_folder_id, user_id=user_id).first()
        if not folder:
            return error_response("NOT_FOUND", "文件夹不存在", status=404)

    old_folder_id = material.folder_id
    if old_folder_id == target_folder_id:
        return jsonify(
            {
                "message": "资料已在目标文件夹",
                "changed": False,
                "sync_state": "synced",
                "material": material.to_dict(),
                "folder_counts": _folder_counts(user_id, {old_folder_id, target_folder_id}),
            }
        )

    material.folder_id = target_folder_id
    material.sync_state = "synced"
    MaterialVisualAsset.query.filter_by(user_id=user_id, material_id=material.id).update({"folder_id": target_folder_id})
    db.session.flush()

    try:
        RAGService().sync_material_folder_metadata(material)
        material.sync_state = "synced"
        if material.status == "ready" and material.index_state == "stale":
            material.index_state = "ready"
        db.session.commit()
        return jsonify(
            {
                "message": "资料已移动到文件夹" if target_folder_id else "资料已移回未分类",
                "changed": True,
                "sync_state": "synced",
                "material": material.to_dict(),
                "folder_counts": _folder_counts(user_id, {old_folder_id, target_folder_id}),
            }
        )
    except Exception:
        current_app.logger.warning("Vector metadata sync failed after material move", exc_info=True)
        material.sync_state = "sync_failed"
        material.index_state = "stale"
        db.session.commit()
        return jsonify(
            {
                "message": "资料已移动，但索引同步失败，可重建索引修复检索范围",
                "changed": True,
                "sync_state": "sync_failed",
                "error_code": "VECTOR_SYNC_FAILED",
                "retryable": True,
                "material": material.to_dict(),
                "folder_counts": _folder_counts(user_id, {old_folder_id, target_folder_id}),
            }
        )
```

- [ ] **Step 5: Run endpoint tests**

Run:

```powershell
python -m pytest tests/test_material_move_scope.py::test_move_uncategorized_material_to_folder tests/test_material_move_scope.py::test_move_material_sync_failure_marks_stale_but_keeps_sql_change -v
```

Expected: PASS after `RAGService.sync_material_folder_metadata` is added in the next task, or FAIL with missing method until then.

---

### Task 2: Add RAG projection sync and SQL-validated scope retrieval

**Files:**
- Modify: `backend/services/rag_service.py`
- Modify: `backend/services/vector_store_service.py`
- Test: `backend/tests/test_material_move_scope.py`

- [ ] **Step 1: Add failing tests for folder scope consistency**

Append to `backend/tests/test_material_move_scope.py`:

```python
from services.rag_service import RAGService


def test_fallback_search_uses_live_sql_folder_after_move(app, make_user, make_folder, make_material, make_chunk):
    user = make_user()
    old_folder = make_folder(user, name="旧文件夹")
    new_folder = make_folder(user, name="新文件夹")
    material = make_material(user, folder=old_folder, status="ready")
    make_chunk(material, content="事实表围绕业务过程建立")

    material.folder_id = new_folder.id
    db.session.commit()

    rag = RAGService()
    old_refs = rag._fallback_search(user.id, "事实表", None, old_folder.id, 5)
    new_refs = rag._fallback_search(user.id, "事实表", None, new_folder.id, 5)

    assert old_refs == []
    assert len(new_refs) == 1
    assert new_refs[0]["folder_id"] == new_folder.id
    assert new_refs[0]["folder_name"] == "新文件夹"


def test_sync_material_folder_metadata_updates_visual_rows_and_calls_vector_services(app, make_user, make_folder, make_material, make_visual_asset):
    user = make_user()
    folder = make_folder(user)
    material = make_material(user, folder=folder, status="ready")
    asset = make_visual_asset(material, status="ready")

    with patch.object(RAGService, "__init__", lambda self: None):
        rag = RAGService()
        rag.vector_store = type("Store", (), {"update_metadata_where": lambda self, where, metadata: None})()
        rag.visual_store = type("Store", (), {"update_metadata_where": lambda self, where, metadata: None})()
        rag.sync_material_folder_metadata(material)

    db.session.refresh(asset)
    assert asset.folder_id == folder.id
```

- [ ] **Step 2: Run tests to verify missing helper fails**

Run:

```powershell
python -m pytest tests/test_material_move_scope.py::test_sync_material_folder_metadata_updates_visual_rows_and_calls_vector_services -v
```

Expected: FAIL because `sync_material_folder_metadata` is not defined.

- [ ] **Step 3: Add vector metadata update helper**

In `backend/services/vector_store_service.py`, add:

```python
    def update_metadata_where(self, where, metadata):
        rows = self.collection.get(where=where, include=["documents", "embeddings", "metadatas"])
        ids = rows.get("ids") or []
        if not ids:
            return
        documents = rows.get("documents") or []
        embeddings = rows.get("embeddings") or []
        metadatas = rows.get("metadatas") or []
        updated_metadatas = [{**(item or {}), **metadata} for item in metadatas]
        self.collection.upsert(ids=ids, documents=documents, embeddings=embeddings, metadatas=updated_metadatas)
```

- [ ] **Step 4: Add RAG projection sync helper**

In `backend/services/rag_service.py`, add this method to `RAGService`:

```python
    def sync_material_folder_metadata(self, material):
        folder_name = material.folder.name if material.folder else ""
        folder_id = material.folder_id or 0
        metadata = {"folder_id": folder_id, "folder_name": folder_name}
        where = {"$and": [{"user_id": material.user_id}, {"material_id": material.id}]}
        self.vector_store.update_metadata_where(where, metadata)
        self.visual_store.update_metadata_where(where, metadata)
        MaterialVisualAsset.query.filter_by(user_id=material.user_id, material_id=material.id).update(
            {"folder_id": material.folder_id}
        )
        return True
```

- [ ] **Step 5: Run RAG tests**

Run:

```powershell
python -m pytest tests/test_material_move_scope.py::test_fallback_search_uses_live_sql_folder_after_move tests/test_material_move_scope.py::test_sync_material_folder_metadata_updates_visual_rows_and_calls_vector_services -v
```

Expected: PASS.

---

### Task 3: Reconcile folder delete with stale vector metadata

**Files:**
- Modify: `backend/routes/folders.py`
- Test: `backend/tests/test_material_move_scope.py`

- [ ] **Step 1: Write failing test**

Append to `backend/tests/test_material_move_scope.py`:

```python
def test_delete_folder_moves_materials_uncategorized_and_marks_projection_stale(client, auth_headers, make_folder, make_material):
    headers, user = auth_headers()
    folder = make_folder(user)
    material = make_material(user, folder=folder, status="ready")

    response = client.delete(f"/api/material-folders/{folder.id}", headers=headers)

    assert response.status_code == 200
    db.session.refresh(material)
    assert material.folder_id is None
    assert material.sync_state in {"sync_pending", "sync_failed", "synced"}
    assert material.index_state in {"stale", "ready"}
```

- [ ] **Step 2: Run test**

Run:

```powershell
python -m pytest tests/test_material_move_scope.py::test_delete_folder_moves_materials_uncategorized_and_marks_projection_stale -v
```

Expected: FAIL until folder delete marks moved rows.

- [ ] **Step 3: Implement folder delete stale marking**

In `backend/routes/folders.py`, replace the existing update line with:

```python
    affected = Material.query.filter_by(user_id=user_id, folder_id=folder_id).all()
    for material in affected:
        material.folder_id = None
        material.sync_state = "sync_pending"
        if material.status == "ready":
            material.index_state = "stale"
```

Keep the delete and commit lines after this block.

- [ ] **Step 4: Run test**

Run:

```powershell
python -m pytest tests/test_material_move_scope.py::test_delete_folder_moves_materials_uncategorized_and_marks_projection_stale -v
```

Expected: PASS.

---

### Task 4: Add frontend API and move controls

**Files:**
- Modify: `frontend/src/api/modules.js`
- Modify: `frontend/src/components/study/MaterialCard.vue`
- Modify: `frontend/src/views/Materials.vue`

- [ ] **Step 1: Add API method**

In `frontend/src/api/modules.js`, change the material API object so it includes:

```javascript
  moveFolder: (id, data) => http.patch(`/materials/${id}/folder`, data),
```

Place it after `remove` and before `reindex`.

- [ ] **Step 2: Add card emit and button**

In `frontend/src/components/study/MaterialCard.vue`, add `move` to the component emits:

```javascript
const emit = defineEmits(['view', 'ask', 'reindex', 'remove', 'move'])
```

Add a visible action button near existing material actions:

```vue
<el-button @click="emit('move', material)">{{ material.folder_id ? '移动到文件夹' : '归类到文件夹' }}</el-button>
```

- [ ] **Step 3: Wire card and table move actions**

In `frontend/src/views/Materials.vue`, update `MaterialCard` usage:

```vue
@move="openMoveDialog"
```

In the table operation column, keep `查看` and `问答` as visible primary actions, and add a keyboard-accessible more menu:

```vue
<el-dropdown trigger="click" @command="(command) => handleMaterialCommand(command, row)">
  <el-button :icon="MoreFilled" aria-label="更多资料操作">更多</el-button>
  <template #dropdown>
    <el-dropdown-menu>
      <el-dropdown-item command="move">{{ row.folder_id ? '移动到文件夹' : '归类到文件夹' }}</el-dropdown-item>
      <el-dropdown-item command="reindex">重建索引</el-dropdown-item>
      <el-dropdown-item command="delete" divided>删除资料</el-dropdown-item>
    </el-dropdown-menu>
  </template>
</el-dropdown>
```

Import `MoreFilled` from `@element-plus/icons-vue`.

- [ ] **Step 4: Add move dialog state and submit logic**

In `frontend/src/views/Materials.vue` script, add:

```javascript
const moveDialog = ref(false)
const movingMaterial = ref(null)
const moving = ref(false)
const moveTargetFolderId = ref(null)

function openMoveDialog(material) {
  movingMaterial.value = material
  moveTargetFolderId.value = material.folder_id ?? null
  moveDialog.value = true
}

async function submitMoveMaterial() {
  if (!movingMaterial.value) return
  moving.value = true
  try {
    const result = await materialApi.moveFolder(movingMaterial.value.id, {
      folder_id: moveTargetFolderId.value,
      request_id: `move_${Date.now()}`
    })
    const index = allMaterials.value.findIndex((item) => item.id === result.material.id)
    if (index >= 0) allMaterials.value[index] = result.material
    if (result.sync_state === 'sync_failed') ElMessage.warning(result.message)
    else ElMessage.success(result.message || '资料已移动')
    moveDialog.value = false
    await loadFolders()
  } finally {
    moving.value = false
  }
}

function handleMaterialCommand(command, row) {
  if (command === 'move') openMoveDialog(row)
  if (command === 'reindex') reindex(row)
  if (command === 'delete') removeMaterial(row)
}
```

Add this dialog below the upload dialog:

```vue
<el-dialog v-model="moveDialog" :title="movingMaterial?.folder_id ? '移动资料' : '归类资料'" width="420px">
  <el-form label-position="top">
    <el-form-item label="目标文件夹">
      <el-select v-model="moveTargetFolderId" clearable placeholder="未分类">
        <el-option :value="null" label="未分类" />
        <el-option v-for="folder in folders" :key="folder.id" :value="folder.id" :label="folder.name" />
      </el-select>
    </el-form-item>
  </el-form>
  <template #footer>
    <el-button @click="moveDialog = false">取消</el-button>
    <el-button type="primary" :loading="moving" :disabled="moveTargetFolderId === (movingMaterial?.folder_id ?? null)" @click="submitMoveMaterial">确认移动</el-button>
  </template>
</el-dialog>
```

- [ ] **Step 5: Build frontend**

Run:

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong\frontend"
npm run build
Pop-Location
```

Expected: PASS.

---

### Task 5: Full verification and commit

**Files:**
- Backend and frontend files changed above.

- [ ] **Step 1: Run backend plan tests**

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong\backend"
python -m pytest tests/test_material_move_scope.py -v
Pop-Location
```

Expected: PASS.

- [ ] **Step 2: Run existing backend regression tests relevant to materials**

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong\backend"
python -m pytest tests/test_materials_api.py -v
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
git add backend/routes/materials.py backend/routes/folders.py backend/services/rag_service.py backend/services/vector_store_service.py backend/tests/test_material_move_scope.py frontend/src/api/modules.js frontend/src/views/Materials.vue frontend/src/components/study/MaterialCard.vue
git commit -m "feat: add material folder move flow"
```

---

## Self-review checklist

- Spec coverage: covers material classification/move to folder, move back to `folder_id: null`, table/card entry points, folder delete reconciliation, and SQL-first RAG folder consistency.
- Independent testability: backend tests can run with mocked vector sync; frontend can be verified by `npm run build` without reindex jobs or persistent chat.
- Intentional deferrals: visual polish of table layout continues in the frontend plan; job-based reindex uses this move/sync foundation in the next plan.
