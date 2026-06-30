# Personal Learning System Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the approved minimum shippable redesign: a warm AI learning workbench with 今日驾驶舱, 知识库, AI 学习会话, 学习计划, and 个人设置, while preserving existing routes and compatibility.

**Architecture:** Implement backend contract/support fields first so frontend pages can rely on explicit scope, status, filter, and summary data. Then add small reusable Vue presentation components under one directory and refactor each existing view in place; do not introduce new top-level routes or a new state library. Keep Phase 3+ features (real chat conversation tables, AI plan persistence, quizzes/flashcards/mastery, async upload queue) out of this implementation.

**Tech Stack:** Flask 3, Flask-SQLAlchemy, Flask-JWT-Extended, pytest, Vue 3 `<script setup>`, Vue Router, Pinia auth store, Element Plus, ECharts, Axios.

---

## Scope and source spec

Approved design spec: `docs/superpowers/specs/2026-06-08-personal-learning-system-redesign-design.md`.

This plan implements:

- Phase 1: minimum shippable visual and interaction redesign.
- Phase 2: lightweight backend fields, filters, computed summaries, date validation, and frontend fallbacks.

This plan does not implement:

- `ChatConversation` / `ChatMessage` persistence tables.
- AI-generated plan preview persistence.
- Quiz, flashcard, mastery, spaced repetition, teacher/admin roles, notification/reminder systems.
- Async upload queue or polling jobs.

---

## File structure and responsibilities

### Backend

- Create: `backend/requirements-dev.txt`  
  Adds pytest for backend red/green tests.

- Create: `backend/tests/conftest.py`  
  Provides isolated Flask app, in-memory SQLite database, JWT header helper, and factories for users, folders, materials, assets, plans, tasks, and chat rows.

- Create: `backend/tests/test_materials_api.py`  
  Drives material schema fields, folder counts, material filters, sorting, and processing error behavior.

- Create: `backend/tests/test_tasks_plans_api.py`  
  Drives date validation, unified task query endpoint, complete/undo behavior, and plan/task computed fields.

- Create: `backend/tests/test_chat_stats_api.py`  
  Drives explicit chat scope contract, reference normalization, legacy compatibility, and dashboard enhanced stats.

- Modify: `backend/models/material.py`  
  Adds `Material.updated_at`, `Material.error_message`, material list metadata, visual asset counts, preview asset id, and enriched folder counts.

- Modify: `backend/services/schema_service.py`  
  Adds idempotent startup compatibility for `material.updated_at` and `material.error_message` while preserving the existing `folder_id` patch.

- Modify: `backend/routes/materials.py`  
  Adds `GET /api/materials` filters and sorting, user-owned `folder_id` validation, `has_visual_assets`, synchronous upload behavior with `error_message`, and success reindex error clearing.

- Modify: `backend/routes/folders.py`  
  Returns enriched folder counts in list/create/update responses.

- Modify: `backend/models/plan.py`  
  Adds computed `StudyTask` fields and `StudyPlan` progress/status fields without schema changes.

- Modify: `backend/routes/tasks.py`  
  Adds `GET /api/tasks`, shared date validation, query filters, and robust 400/404 behavior while preserving `/api/tasks/today`.

- Modify: `backend/routes/plans.py`  
  Adds shared date validation and keeps enriched `StudyPlan.to_dict(include_tasks=True)` responses.

- Modify: `backend/routes/chat.py`  
  Accepts explicit `scope_type`, preserves omitted-scope legacy behavior, and persists current `ChatHistory` only.

- Modify: `backend/services/rag_service.py`  
  Supports `scope_type=general|all|folder|material`, validates readiness/ownership, and normalizes references with legacy-compatible fields.

- Modify: `backend/services/stats_service.py`  
  Adds `today_focus`, `knowledge_health`, `active_plan_summary`, `next_actions`, and `ai_continuity` while preserving old dashboard fields.

### Frontend

- Modify: `frontend/src/api/modules.js`  
  Adds `taskApi.list(params)`, optional dormant chat conversation methods, `planApi.list(params = {})`, and keeps existing methods compatible.

- Modify: `frontend/src/components/AppLayout.vue`  
  Renames authenticated navigation to 今日驾驶舱 / 知识库 / AI 学习会话 / 学习计划 / 个人设置 and shows the current study goal.

- Create: `frontend/src/components/study/PageHeader.vue`  
  Shared page title/subtitle/actions shell.

- Create: `frontend/src/components/study/WorkbenchPanel.vue`  
  Shared warm panel/card wrapper.

- Create: `frontend/src/components/study/MetricCard.vue`  
  Shared dashboard/summary metric card.

- Create: `frontend/src/components/study/StatusBadge.vue`  
  Central code-to-Chinese-label status/tone mapping.

- Create: `frontend/src/components/study/EmptyGuide.vue`  
  Guided empty state with one primary action.

- Create: `frontend/src/components/study/MaterialCard.vue`  
  Card-mode material display and actions.

- Create: `frontend/src/components/study/FolderShelf.vue`  
  Folder rail/shelf with all/uncategorized/user-folder selection and counts.

- Create: `frontend/src/components/study/MaterialFilters.vue`  
  Search/status/type/visual/sort/view-mode controls.

- Create: `frontend/src/components/study/UploadMaterialDialog.vue`  
  Synchronous upload dialog that emits selected file/folder and displays processing copy.

- Create: `frontend/src/components/study/VisualAssetGrid.vue`  
  Authenticated blob visual asset display with ObjectURL cleanup and missing-image placeholders.

- Create: `frontend/src/components/study/ScopeSelector.vue`  
  Chat scope selector for `general|all|folder|material`.

- Create: `frontend/src/components/study/EvidencePanel.vue`  
  Chat evidence/reference panel that accepts both legacy and normalized references and loads visual evidence blobs.

- Create: `frontend/src/components/study/MessageBubble.vue`  
  User/assistant/error bubble display.

- Create: `frontend/src/components/study/PlanCard.vue`  
  Plan card with progress/status/next task and actions.

- Create: `frontend/src/components/study/TaskCard.vue`  
  Task card with due labels, complete/undo/delete actions, and accessible buttons.

- Create: `frontend/src/components/study/TaskBoard.vue`  
  Four-lane board: 今日、即将到期、未安排、已完成.

- Modify: `frontend/src/views/Dashboard.vue`  
  Redesigns dashboard as 今日学习驾驶舱 using enhanced stats plus fallbacks.

- Modify: `frontend/src/views/Materials.vue`  
  Redesigns knowledge library with default card mode, table mode, filters, URL query support, upload and folder CRUD.

- Modify: `frontend/src/views/MaterialDetail.vue`  
  Redesigns detail page as knowledge object with health metrics, visual assets, chunks, and prompt-prefill chat links.

- Modify: `frontend/src/views/Chat.vue`  
  Redesigns three-column AI 学习会话 with explicit `scope_type`, old-history read-only list, pending lock, retry, and evidence panel.

- Modify: `frontend/src/views/Plans.vue`  
  Redesigns plans as today focus + plan cards + four-lane task board with `/plans/:id` and `task_scope` support.

- Modify: `frontend/src/views/Profile.vue`  
  Keeps backend profile save and adds localStorage study preferences and data/AI notes.

- Modify: `frontend/src/styles.css`  
  Adds warm workbench classes, responsive breakpoints, status/evidence/task/card styles, focus states, and reduced-motion support.

---

## Task 0: Baseline protection and current diff review

**Files:**
- Read-only inspection: all currently modified frontend files and docs.

- [ ] **Step 1: Inspect git status before editing**

Run from `D:\学习资料\大数据综合实践\zonghexitong`:

```powershell
git status --short
```

Expected: the existing frontend files may already be modified. Do not discard or overwrite those changes.

- [ ] **Step 2: Inspect the working diff for files this plan will touch**

Run:

```powershell
git diff -- frontend/src/components/AppLayout.vue frontend/src/styles.css frontend/src/views/Dashboard.vue frontend/src/views/Materials.vue frontend/src/views/MaterialDetail.vue frontend/src/views/Chat.vue frontend/src/views/Plans.vue frontend/src/views/Profile.vue
```

Expected: understand the existing warm redesign edits before applying implementation tasks.

- [ ] **Step 3: Record baseline note in the execution log**

Add this note to the executor's progress comments:

```text
Baseline reviewed. Existing frontend working-tree changes are treated as user work and will be preserved by editing incrementally rather than replacing files blindly.
```

- [ ] **Step 4: No commit for read-only baseline**

Do not commit this task. It is a guardrail task.

---

## Task 1: Backend pytest harness

**Files:**
- Create: `backend/requirements-dev.txt`
- Create: `backend/tests/conftest.py`

- [ ] **Step 1: Create backend dev requirements**

Create `backend/requirements-dev.txt` with:

```text
pytest==8.2.2
```

- [ ] **Step 2: Create the pytest fixture file**

Create `backend/tests/conftest.py` with:

```python
import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("AUTO_CREATE_TABLES", "true")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret")
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("UPLOAD_FOLDER", "./test_uploads")
os.environ.setdefault("CHROMA_DIR", "./test_chroma_store")
os.environ.setdefault("AI_API_KEY", "")
os.environ.setdefault("CHAT_API_KEY", "")
os.environ.setdefault("TEXT_EMBEDDING_API_KEY", "")
os.environ.setdefault("MULTIMODAL_EMBEDDING_API_KEY", "")

from datetime import date, datetime, timedelta

import pytest
from flask_jwt_extended import create_access_token

from app import create_app
from extensions import db
from models.chat import ChatHistory
from models.material import Material, MaterialFolder, MaterialChunk, MaterialVisualAsset
from models.plan import StudyPlan, StudyTask
from models.user import User


@pytest.fixture()
def app():
    app = create_app()
    app.config.update(TESTING=True)
    with app.app_context():
        db.drop_all()
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def make_user(app):
    def _make(username="alice"):
        user = User(username=username, nickname=username)
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()
        return user
    return _make


@pytest.fixture()
def auth_headers(app, make_user):
    def _headers(user=None):
        user = user or make_user()
        token = create_access_token(identity=str(user.id))
        return {"Authorization": f"Bearer {token}"}, user
    return _headers


@pytest.fixture()
def make_folder(app):
    def _make(user, name="课程资料", description=""):
        folder = MaterialFolder(user_id=user.id, name=name, description=description)
        db.session.add(folder)
        db.session.commit()
        return folder
    return _make


@pytest.fixture()
def make_material(app):
    def _make(user, folder=None, title="资料", status="ready", file_type="txt", keywords="索引,事务"):
        material = Material(
            user_id=user.id,
            folder_id=folder.id if folder else None,
            title=title,
            file_name=f"{title}.{file_type}",
            file_path=f"/tmp/{title}.{file_type}",
            file_type=file_type,
            summary=f"{title} 摘要",
            keywords=keywords,
            status=status,
        )
        db.session.add(material)
        db.session.commit()
        return material
    return _make


@pytest.fixture()
def make_chunk(app):
    def _make(material, index=0, content="索引是一种帮助数据库快速定位记录的数据结构"):
        chunk = MaterialChunk(
            material_id=material.id,
            chunk_index=index,
            content=content,
            chroma_id=f"chunk-{material.id}-{index}",
        )
        db.session.add(chunk)
        db.session.commit()
        return chunk
    return _make


@pytest.fixture()
def make_visual_asset(app):
    def _make(material, index=0, status="ready"):
        asset = MaterialVisualAsset(
            user_id=material.user_id,
            material_id=material.id,
            folder_id=material.folder_id,
            asset_type="page_image",
            asset_index=index,
            page_number=index + 1,
            caption="图表说明",
            image_path=f"/tmp/asset-{material.id}-{index}.png",
            chroma_id=f"asset-{material.id}-{index}",
            status=status,
            error_message="" if status == "ready" else "视觉索引失败",
        )
        db.session.add(asset)
        db.session.commit()
        return asset
    return _make


@pytest.fixture()
def make_plan(app):
    def _make(user, title="复习计划", start_date=None, end_date=None):
        plan = StudyPlan(
            user_id=user.id,
            title=title,
            description="计划说明",
            start_date=start_date,
            end_date=end_date,
        )
        db.session.add(plan)
        db.session.commit()
        return plan
    return _make


@pytest.fixture()
def make_task(app):
    def _make(user, plan=None, title="学习任务", due_date=None, status="todo", completed_at=None):
        task = StudyTask(
            user_id=user.id,
            plan_id=plan.id if plan else None,
            title=title,
            description="任务说明",
            due_date=due_date,
            status=status,
            completed_at=completed_at,
        )
        db.session.add(task)
        db.session.commit()
        return task
    return _make


@pytest.fixture()
def make_chat(app):
    def _make(user, question="问题", answer="答案", material=None, references_json="[]"):
        row = ChatHistory(
            user_id=user.id,
            material_id=material.id if material else None,
            question=question,
            answer=answer,
            references_json=references_json,
        )
        db.session.add(row)
        db.session.commit()
        return row
    return _make


def iso_today():
    return date.today()


def days_from_today(offset):
    return date.today() + timedelta(days=offset)


def utc_now():
    return datetime.utcnow()
```

- [ ] **Step 3: Install backend test dependencies**

Run:

```powershell
Set-Location "D:\学习资料\大数据综合实践\zonghexitong\backend"
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
```

Expected: packages install without import errors.

- [ ] **Step 4: Run pytest collection**

Run:

```powershell
Set-Location "D:\学习资料\大数据综合实践\zonghexitong\backend"
python -m pytest tests -q
```

Expected: pytest reports no tests collected or passes fixture import without crashing. If it imports application modules successfully, the harness is ready.

- [ ] **Step 5: Commit the test harness**

Run:

```powershell
git add backend/requirements-dev.txt backend/tests/conftest.py
git commit -m @'
test: add backend redesign test harness

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
'@
```

---

## Task 2: Material schema fields and serialization

**Files:**
- Create/modify test: `backend/tests/test_materials_api.py`
- Modify: `backend/models/material.py`
- Modify: `backend/services/schema_service.py`

- [ ] **Step 1: Write failing material serialization tests**

Create `backend/tests/test_materials_api.py` with these tests:

```python
from sqlalchemy import inspect

from extensions import db
from models.material import Material, MaterialFolder


def test_material_to_dict_includes_phase2_fields_and_counts(app, make_user, make_folder, make_material, make_chunk, make_visual_asset):
    user = make_user()
    folder = make_folder(user)
    material = make_material(user, folder=folder, title="数据库讲义", status="ready")
    make_chunk(material, index=0)
    make_chunk(material, index=1)
    ready_asset = make_visual_asset(material, index=0, status="ready")
    make_visual_asset(material, index=1, status="failed")

    data = material.to_dict()

    assert data["updated_at"] == data["created_at"]
    assert data["error_message"] == ""
    assert data["chunk_count"] == 2
    assert data["visual_asset_count"] == 2
    assert data["ready_visual_asset_count"] == 1
    assert data["failed_visual_asset_count"] == 1
    assert data["preview_asset_id"] == ready_asset.id


def test_folder_to_dict_includes_status_counts(app, make_user, make_folder, make_material):
    user = make_user()
    folder = make_folder(user)
    make_material(user, folder=folder, status="ready")
    make_material(user, folder=folder, status="processing")
    make_material(user, folder=folder, status="failed")

    data = folder.to_dict(include_count=True)

    assert data["material_count"] == 3
    assert data["ready_count"] == 1
    assert data["processing_count"] == 1
    assert data["failed_count"] == 1


def test_schema_compatibility_adds_material_updated_at_and_error_message(app):
    inspector = inspect(db.engine)
    columns = {column["name"] for column in inspector.get_columns("material")}

    assert "updated_at" in columns
    assert "error_message" in columns
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
Set-Location "D:\学习资料\大数据综合实践\zonghexitong\backend"
python -m pytest tests\test_materials_api.py -q
```

Expected: FAIL because `updated_at`, `error_message`, visual/count fields, or folder status counts are missing.

- [ ] **Step 3: Add model fields and serialization**

Modify `backend/models/material.py` as follows.

Add these fields to `Material` after `status`:

```python
    error_message = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
```

Replace `Material.to_dict()` with:

```python
    def to_dict(self, include_chunks=False):
        ready_assets = [asset for asset in self.visual_assets if asset.status == "ready"]
        failed_assets = [asset for asset in self.visual_assets if asset.status == "failed"]
        preview_asset = ready_assets[0] if ready_assets else None
        created_at = self.created_at.isoformat() if self.created_at else None
        updated_at = self.updated_at.isoformat() if getattr(self, "updated_at", None) else created_at
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "folder_id": self.folder_id,
            "folder_name": self.folder.name if self.folder else "",
            "title": self.title,
            "file_name": self.file_name,
            "file_type": self.file_type,
            "summary": self.summary,
            "keywords": [item for item in (self.keywords or "").split(",") if item],
            "status": self.status,
            "error_message": getattr(self, "error_message", "") or "",
            "created_at": created_at,
            "updated_at": updated_at,
            "chunk_count": len(self.chunks),
            "visual_asset_count": len(self.visual_assets),
            "ready_visual_asset_count": len(ready_assets),
            "failed_visual_asset_count": len(failed_assets),
            "preview_asset_id": preview_asset.id if preview_asset else None,
        }
        if include_chunks:
            data["chunks"] = [chunk.to_dict() for chunk in self.chunks]
            data["visual_assets"] = [asset.to_dict() for asset in self.visual_assets]
        return data
```

Replace the `if include_count:` block in `MaterialFolder.to_dict()` with:

```python
        if include_count:
            data["material_count"] = len(self.materials)
            data["ready_count"] = len([item for item in self.materials if item.status == "ready"])
            data["processing_count"] = len([item for item in self.materials if item.status == "processing"])
            data["failed_count"] = len([item for item in self.materials if item.status == "failed"])
```

- [ ] **Step 4: Add schema compatibility columns**

Replace `backend/services/schema_service.py` with:

```python
from sqlalchemy import inspect, text

from extensions import db


def ensure_schema_compatibility(app):
    with app.app_context():
        db.create_all()
        inspector = inspect(db.engine)
        if not inspector.has_table("material"):
            return

        columns = {column["name"] for column in inspector.get_columns("material")}
        dialect = db.engine.dialect.name

        statements = []
        if "folder_id" not in columns:
            if dialect == "mysql":
                statements.append("ALTER TABLE material ADD COLUMN folder_id INT NULL, ADD INDEX ix_material_folder_id (folder_id)")
            else:
                statements.append("ALTER TABLE material ADD COLUMN folder_id INTEGER")

        if "error_message" not in columns:
            if dialect == "mysql":
                statements.append("ALTER TABLE material ADD COLUMN error_message TEXT")
            else:
                statements.append("ALTER TABLE material ADD COLUMN error_message TEXT DEFAULT ''")

        if "updated_at" not in columns:
            if dialect == "mysql":
                statements.append("ALTER TABLE material ADD COLUMN updated_at DATETIME NULL")
            else:
                statements.append("ALTER TABLE material ADD COLUMN updated_at DATETIME")

        for statement in statements:
            db.session.execute(text(statement))

        if "updated_at" not in columns:
            db.session.execute(text("UPDATE material SET updated_at = created_at WHERE updated_at IS NULL"))
        if "error_message" not in columns:
            db.session.execute(text("UPDATE material SET error_message = '' WHERE error_message IS NULL"))

        db.session.commit()
```

- [ ] **Step 5: Run material tests again**

Run:

```powershell
Set-Location "D:\学习资料\大数据综合实践\zonghexitong\backend"
python -m pytest tests\test_materials_api.py -q
```

Expected: PASS for the serialization and schema tests.

- [ ] **Step 6: Commit material schema fields**

Run:

```powershell
git add backend/tests/test_materials_api.py backend/models/material.py backend/services/schema_service.py
git commit -m @'
feat: add material phase 2 schema fields

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
'@
```

---

## Task 3: Material processing errors, filters, and folder counts

**Files:**
- Modify: `backend/tests/test_materials_api.py`
- Modify: `backend/routes/materials.py`
- Modify: `backend/routes/folders.py`

- [ ] **Step 1: Add failing material API tests**

Append these tests to `backend/tests/test_materials_api.py`:

```python
from datetime import datetime
from unittest.mock import patch

import pytest

from extensions import db
from models.material import Material


def test_material_folders_return_status_counts(client, auth_headers, make_folder, make_material):
    headers, user = auth_headers()
    folder = make_folder(user, name="数据库")
    make_material(user, folder=folder, status="ready")
    make_material(user, folder=folder, status="failed")
    make_material(user, folder=folder, status="processing")

    response = client.get("/api/material-folders", headers=headers)

    assert response.status_code == 200
    row = response.get_json()[0]
    assert row["material_count"] == 3
    assert row["ready_count"] == 1
    assert row["failed_count"] == 1
    assert row["processing_count"] == 1


def test_material_list_filters_and_sorts(client, auth_headers, make_folder, make_material, make_chunk, make_visual_asset):
    headers, user = auth_headers()
    folder = make_folder(user, name="数据库")
    ready = make_material(user, folder=folder, title="索引讲义", status="ready", file_type="pdf", keywords="索引,事务")
    failed = make_material(user, folder=None, title="失败资料", status="failed", file_type="txt", keywords="失败")
    make_chunk(ready, index=0)
    make_visual_asset(ready, index=0, status="ready")

    response = client.get("/api/materials?q=索引&status=ready&file_type=pdf&has_visual_assets=true&sort=richness_desc", headers=headers)

    assert response.status_code == 200
    rows = response.get_json()
    assert [row["id"] for row in rows] == [ready.id]
    assert rows[0]["visual_asset_count"] == 1
    assert rows[0]["chunk_count"] == 1
    assert failed.id not in [row["id"] for row in rows]


@pytest.mark.parametrize("query", ["status=done", "has_visual_assets=maybe"])
def test_material_list_invalid_filters_return_400(client, auth_headers, query):
    headers, _user = auth_headers()

    response = client.get(f"/api/materials?{query}", headers=headers)

    assert response.status_code == 400


def test_material_list_cross_user_folder_returns_404(client, auth_headers, make_user, make_folder):
    headers, _user = auth_headers()
    other = make_user("other-user")
    other_folder = make_folder(other, name="别人的文件夹")

    response = client.get(f"/api/materials?folder_id={other_folder.id}", headers=headers)

    assert response.status_code == 404


def test_material_processing_failure_uses_error_message(client, auth_headers, tmp_path):
    headers, _user = auth_headers()
    file_path = tmp_path / "bad.txt"
    file_path.write_text("bad", encoding="utf-8")

    with patch("routes.materials.extract_text", side_effect=RuntimeError("解析失败")):
        with file_path.open("rb") as handle:
            response = client.post(
                "/api/materials/upload",
                headers=headers,
                data={"file": (handle, "bad.txt")},
                content_type="multipart/form-data",
            )

    assert response.status_code == 201
    data = response.get_json()
    assert data["status"] == "failed"
    assert "解析失败" in data["error_message"]
    assert data["summary"] == ""
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
Set-Location "D:\学习资料\大数据综合实践\zonghexitong\backend"
python -m pytest tests\test_materials_api.py -q
```

Expected: FAIL on invalid filter handling, folder ownership, filter/sort implementation, or processing `error_message`.

- [ ] **Step 3: Implement filter helpers in materials route**

Add these helpers near the bottom of `backend/routes/materials.py` above `_process_material`:

```python
VALID_MATERIAL_STATUSES = {"ready", "processing", "failed"}
VALID_MATERIAL_SORTS = {"created_desc", "title_asc", "status", "richness_desc"}


def _parse_bool_arg(name):
    value = request.args.get(name)
    if value is None or value == "":
        return None
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    raise ValueError(f"{name} 必须为 true 或 false")


def _material_richness(material):
    keyword_count = len(material.to_dict().get("keywords", []))
    return len(material.chunks) + len(material.visual_assets) * 3 + min(keyword_count, 5)
```

Replace `list_materials()` in `backend/routes/materials.py` with:

```python
@materials_bp.get("")
@jwt_required()
def list_materials():
    user_id = int(get_jwt_identity())
    folder_id = request.args.get("folder_id")
    q = (request.args.get("q") or "").strip().lower()
    file_type = (request.args.get("file_type") or "").strip().lower()
    status = (request.args.get("status") or "").strip()
    sort = (request.args.get("sort") or "created_desc").strip() or "created_desc"

    if status and status not in VALID_MATERIAL_STATUSES:
        return jsonify({"message": "资料状态参数无效"}), 400
    try:
        has_visual_assets = _parse_bool_arg("has_visual_assets")
    except ValueError as exc:
        return jsonify({"message": str(exc)}), 400

    query = Material.query.filter_by(user_id=user_id)
    if folder_id:
        try:
            folder_id_int = int(folder_id)
        except ValueError:
            return jsonify({"message": "文件夹不存在"}), 404
        folder = MaterialFolder.query.filter_by(id=folder_id_int, user_id=user_id).first()
        if not folder:
            return jsonify({"message": "文件夹不存在"}), 404
        query = query.filter_by(folder_id=folder_id_int)
    if file_type:
        query = query.filter_by(file_type=file_type)
    if status:
        query = query.filter_by(status=status)

    materials = query.all()
    if q:
        materials = [
            material for material in materials
            if q in (material.title or "").lower()
            or q in (material.file_name or "").lower()
            or q in (material.folder.name if material.folder else "").lower()
            or q in (material.summary or "").lower()
            or q in (material.keywords or "").lower()
        ]
    if has_visual_assets is True:
        materials = [material for material in materials if len(material.visual_assets) > 0]
    if has_visual_assets is False:
        materials = [material for material in materials if len(material.visual_assets) == 0]

    warning = None
    if sort not in VALID_MATERIAL_SORTS:
        warning = "排序参数无效，已使用最新上传排序"
        sort = "created_desc"
    if sort == "created_desc":
        materials.sort(key=lambda item: item.created_at or item.id, reverse=True)
    elif sort == "title_asc":
        materials.sort(key=lambda item: item.title.lower())
    elif sort == "status":
        order = {"ready": 0, "processing": 1, "failed": 2}
        materials.sort(key=lambda item: (order.get(item.status, 99), item.title.lower()))
    elif sort == "richness_desc":
        materials.sort(key=lambda item: (_material_richness(item), item.created_at or item.id), reverse=True)

    response = jsonify([material.to_dict() for material in materials])
    if warning:
        response.headers["X-StudyHub-Warning"] = warning
    return response
```

- [ ] **Step 4: Implement error_message behavior in processing**

In `_process_material()` replace the success/failure assignments with this behavior:

```python
        material.error_message = ""
        material.summary = ai.summarize(text)
        material.keywords = ",".join(ai.extract_keywords(text))
        material.status = "ready" if chunks else "failed"
        if not chunks:
            material.error_message = "未提取到可索引的文本内容"
```

Replace the visual failure note block with:

```python
            elif visual_count and not chunks:
                material.status = "failed"
                material.error_message = "视觉资产已提取，但未完成文本或视觉向量索引。请检查多模态 embedding 配置。"
```

Replace the visual exception block with:

```python
        except Exception as visual_exc:
            current_app.logger.warning("Visual assets were not indexed for material %s", material.id, exc_info=True)
            if material.status != "ready":
                material.status = "failed"
            material.error_message = f"视觉索引未完成：{visual_exc}"
```

Replace the outer exception block with:

```python
    except Exception as exc:
        current_app.logger.exception("Failed to process material %s", material.id)
        material.status = "failed"
        material.summary = ""
        material.error_message = f"资料处理失败：{exc}"
        db.session.commit()
```

- [ ] **Step 5: Ensure folder route returns enriched counts**

No major code should be needed if Task 2 changed `MaterialFolder.to_dict(include_count=True)`. Confirm `backend/routes/folders.py` still returns `folder.to_dict(include_count=True)` in list/create/update.

- [ ] **Step 6: Run material API tests**

Run:

```powershell
Set-Location "D:\学习资料\大数据综合实践\zonghexitong\backend"
python -m pytest tests\test_materials_api.py -q
```

Expected: PASS for all material tests.

- [ ] **Step 7: Commit material API filters and errors**

Run:

```powershell
git add backend/tests/test_materials_api.py backend/routes/materials.py backend/routes/folders.py
git commit -m @'
feat: add material library filters

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
'@
```

---

## Task 4: Plan/task computed fields, date validation, and unified task endpoint

**Files:**
- Create: `backend/tests/test_tasks_plans_api.py`
- Modify: `backend/models/plan.py`
- Modify: `backend/routes/tasks.py`
- Modify: `backend/routes/plans.py`

- [ ] **Step 1: Write failing plan/task tests**

Create `backend/tests/test_tasks_plans_api.py` with:

```python
from datetime import date, datetime, timedelta

from extensions import db


def test_plan_to_dict_includes_computed_fields(app, make_user, make_plan, make_task):
    user = make_user()
    plan = make_plan(user, title="数据库复习")
    make_task(user, plan=plan, title="已完成", status="done", completed_at=datetime.utcnow())
    make_task(user, plan=plan, title="待完成", due_date=date.today() + timedelta(days=1), status="todo")

    data = plan.to_dict(include_tasks=True)

    assert data["task_count"] == 2
    assert data["done_count"] == 1
    assert data["todo_count"] == 1
    assert data["progress_percent"] == 50
    assert data["next_due_task"]["title"] == "待完成"
    assert data["status"] == "active"
    assert data["tasks"][0]["plan_title"] == "数据库复习"


def test_plan_status_priority(app, make_user, make_plan, make_task):
    user = make_user()
    completed = make_plan(user, title="完成计划")
    make_task(user, plan=completed, status="done", completed_at=datetime.utcnow())
    overdue = make_plan(user, title="逾期计划")
    make_task(user, plan=overdue, status="todo", due_date=date.today() - timedelta(days=1))
    empty = make_plan(user, title="空计划")
    future = make_plan(user, title="未来计划", start_date=date.today() + timedelta(days=3))

    assert completed.to_dict(include_tasks=True)["status"] == "completed"
    assert overdue.to_dict(include_tasks=True)["status"] == "overdue"
    assert empty.to_dict(include_tasks=True)["status"] == "empty"
    assert future.to_dict(include_tasks=True)["status"] == "empty"


def test_get_tasks_scopes_and_filters(client, auth_headers, make_plan, make_task):
    headers, user = auth_headers()
    plan = make_plan(user)
    today = make_task(user, plan=plan, title="今天", due_date=date.today(), status="todo")
    overdue = make_task(user, plan=plan, title="逾期", due_date=date.today() - timedelta(days=1), status="todo")
    upcoming = make_task(user, plan=plan, title="未来", due_date=date.today() + timedelta(days=2), status="todo")
    unscheduled = make_task(user, plan=plan, title="未安排", due_date=None, status="todo")
    done = make_task(user, plan=plan, title="已完成", due_date=date.today(), status="done", completed_at=datetime.utcnow())

    assert [row["id"] for row in client.get("/api/tasks?scope=today", headers=headers).get_json()] == [today.id, done.id]
    assert [row["id"] for row in client.get("/api/tasks?scope=overdue", headers=headers).get_json()] == [overdue.id]
    assert [row["id"] for row in client.get("/api/tasks?scope=upcoming", headers=headers).get_json()] == [upcoming.id]
    assert [row["id"] for row in client.get("/api/tasks?scope=unscheduled", headers=headers).get_json()] == [unscheduled.id]
    assert [row["id"] for row in client.get("/api/tasks?scope=completed", headers=headers).get_json()] == [done.id]


def test_task_date_validation_returns_400(client, auth_headers):
    headers, _user = auth_headers()

    response = client.post("/api/tasks", headers=headers, json={"title": "坏日期", "due_date": "2026/06/08"})

    assert response.status_code == 400
    assert response.get_json()["message"] == "日期格式必须为 YYYY-MM-DD"


def test_plan_date_validation_returns_400(client, auth_headers):
    headers, _user = auth_headers()

    response = client.post("/api/plans", headers=headers, json={"title": "坏日期", "start_date": "2026-06-10", "end_date": "2026-06-01"})

    assert response.status_code == 400
    assert response.get_json()["message"] == "结束日期不能早于开始日期"


def test_task_plan_id_is_user_scoped(client, auth_headers, make_user, make_plan):
    headers, _user = auth_headers()
    other = make_user("other")
    other_plan = make_plan(other)

    response = client.get(f"/api/tasks?plan_id={other_plan.id}", headers=headers)

    assert response.status_code == 404
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
Set-Location "D:\学习资料\大数据综合实践\zonghexitong\backend"
python -m pytest tests\test_tasks_plans_api.py -q
```

Expected: FAIL because computed fields, `/api/tasks`, and validation are missing.

- [ ] **Step 3: Implement computed task and plan fields**

Modify `backend/models/plan.py`.

Update imports:

```python
from datetime import date, datetime
```

Add helper methods to `StudyPlan` before `to_dict`:

```python
    def _task_summary(self):
        tasks = list(self.tasks)
        done_tasks = [task for task in tasks if task.status == "done"]
        todo_tasks = [task for task in tasks if task.status != "done"]
        overdue_tasks = [task for task in todo_tasks if task.due_date and task.due_date < date.today()]
        next_due = sorted(
            [task for task in todo_tasks if task.due_date],
            key=lambda task: task.due_date,
        )
        if tasks and len(done_tasks) == len(tasks):
            status = "completed"
        elif overdue_tasks:
            status = "overdue"
        elif not tasks:
            status = "empty"
        elif self.start_date and date.today() < self.start_date and not done_tasks:
            status = "not_started"
        else:
            status = "active"
        return {
            "task_count": len(tasks),
            "done_count": len(done_tasks),
            "todo_count": len(todo_tasks),
            "progress_percent": round(len(done_tasks) / len(tasks) * 100) if tasks else 0,
            "next_due_task": next_due[0].to_dict() if next_due else None,
            "status": status,
            "overdue_count": len(overdue_tasks),
        }
```

In `StudyPlan.to_dict()`, before `if include_tasks:`, add:

```python
        data.update(self._task_summary())
```

Replace `StudyTask.to_dict()` with:

```python
    def to_dict(self):
        today = date.today()
        is_overdue = self.status != "done" and self.due_date is not None and self.due_date < today
        days_until_due = (self.due_date - today).days if self.due_date else None
        return {
            "id": self.id,
            "plan_id": self.plan_id,
            "plan_title": self.plan.title if self.plan else "",
            "user_id": self.user_id,
            "title": self.title,
            "description": self.description,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "status": self.status,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_overdue": is_overdue,
            "days_until_due": days_until_due,
        }
```

- [ ] **Step 4: Implement date helpers and `/api/tasks`**

In `backend/routes/tasks.py`, add:

```python
VALID_TASK_SCOPES = {"today", "overdue", "upcoming", "unscheduled", "completed"}
VALID_TASK_STATUSES = {"todo", "done"}


def _parse_date_or_error(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError("日期格式必须为 YYYY-MM-DD")
```

Add this route above `today_tasks()`:

```python
@tasks_bp.get("")
@jwt_required()
def list_tasks():
    user_id = int(get_jwt_identity())
    query = StudyTask.query.filter_by(user_id=user_id)
    today = date.today()

    scope = (request.args.get("scope") or "").strip()
    status = (request.args.get("status") or "").strip()
    plan_id = request.args.get("plan_id")

    if scope and scope not in VALID_TASK_SCOPES:
        return jsonify({"message": "任务范围参数无效"}), 400
    if status and status not in VALID_TASK_STATUSES:
        return jsonify({"message": "任务状态参数无效"}), 400
    if plan_id:
        try:
            plan_id_int = int(plan_id)
        except ValueError:
            return jsonify({"message": "学习计划不存在"}), 404
        if not StudyPlan.query.filter_by(id=plan_id_int, user_id=user_id).first():
            return jsonify({"message": "学习计划不存在"}), 404
        query = query.filter_by(plan_id=plan_id_int)
    if status:
        query = query.filter_by(status=status)

    try:
        from_date = _parse_date_or_error(request.args.get("from"))
        to_date = _parse_date_or_error(request.args.get("to"))
    except ValueError as exc:
        return jsonify({"message": str(exc)}), 400
    if from_date and to_date and to_date < from_date:
        return jsonify({"message": "结束日期不能早于开始日期"}), 400
    if from_date:
        query = query.filter(StudyTask.due_date >= from_date)
    if to_date:
        query = query.filter(StudyTask.due_date <= to_date)

    if scope == "today":
        query = query.filter(StudyTask.due_date == today)
    elif scope == "overdue":
        query = query.filter(StudyTask.status == "todo", StudyTask.due_date < today)
    elif scope == "upcoming":
        query = query.filter(StudyTask.status == "todo", StudyTask.due_date > today)
    elif scope == "unscheduled":
        query = query.filter(StudyTask.status == "todo", StudyTask.due_date.is_(None))
    elif scope == "completed":
        query = query.filter(StudyTask.status == "done")

    tasks = query.order_by(StudyTask.due_date.is_(None), StudyTask.due_date.asc(), StudyTask.created_at.desc()).all()
    return jsonify([task.to_dict() for task in tasks])
```

Update `_parse_date()` in `backend/routes/tasks.py`:

```python
def _parse_date(value):
    return _parse_date_or_error(value)
```

Wrap create/update date parsing in `try/except`:

```python
    try:
        due_date = _parse_date(data.get("due_date"))
    except ValueError as exc:
        return jsonify({"message": str(exc)}), 400
```

Use `due_date=due_date` in the task constructor/update.

- [ ] **Step 5: Implement plan date validation**

In `backend/routes/plans.py`, add:

```python
def _parse_date_or_error(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError("日期格式必须为 YYYY-MM-DD")


def _parse_plan_dates(data):
    start_date = _parse_date_or_error(data.get("start_date"))
    end_date = _parse_date_or_error(data.get("end_date"))
    if start_date and end_date and end_date < start_date:
        raise ValueError("结束日期不能早于开始日期")
    return start_date, end_date
```

In `create_plan()` and `update_plan()`, replace direct `_parse_date()` calls with:

```python
    try:
        start_date, end_date = _parse_plan_dates(data)
    except ValueError as exc:
        return jsonify({"message": str(exc)}), 400
```

Then assign `start_date=start_date`, `end_date=end_date`.

Remove or leave `_parse_date()` unused only if no code references it; if kept, make it call `_parse_date_or_error()`.

- [ ] **Step 6: Run plan/task tests**

Run:

```powershell
Set-Location "D:\学习资料\大数据综合实践\zonghexitong\backend"
python -m pytest tests\test_tasks_plans_api.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit plan/task API work**

Run:

```powershell
git add backend/tests/test_tasks_plans_api.py backend/models/plan.py backend/routes/tasks.py backend/routes/plans.py
git commit -m @'
feat: add study plan task board data

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
'@
```

---

## Task 5: Chat scope contract, reference normalization, and dashboard stats

**Files:**
- Create: `backend/tests/test_chat_stats_api.py`
- Modify: `backend/routes/chat.py`
- Modify: `backend/services/rag_service.py`
- Modify: `backend/models/chat.py`
- Modify: `backend/services/stats_service.py`

- [ ] **Step 1: Write failing chat/stats tests**

Create `backend/tests/test_chat_stats_api.py` with:

```python
import json
from datetime import date, datetime, timedelta
from unittest.mock import patch

from extensions import db
from models.chat import ChatHistory


def test_chat_general_scope_returns_empty_references(client, auth_headers):
    headers, _user = auth_headers()

    with patch("routes.chat.AIService") as fake_ai:
        fake_ai.return_value.answer.return_value = "通用回答"
        response = client.post("/api/chat", headers=headers, json={"scope_type": "general", "question": "什么是索引？"})

    assert response.status_code == 200
    data = response.get_json()
    assert data["answer"] == "通用回答"
    assert data["references"] == []


def test_chat_all_scope_requires_ready_material(client, auth_headers):
    headers, _user = auth_headers()

    response = client.post("/api/chat", headers=headers, json={"scope_type": "all", "question": "总结资料"})

    assert response.status_code == 400
    assert response.get_json()["message"] == "当前暂无可问答的资料，请先上传并处理资料，或切换为通用问答"


def test_chat_material_scope_rejects_not_ready(client, auth_headers, make_material):
    headers, user = auth_headers()
    material = make_material(user, status="processing")

    response = client.post("/api/chat", headers=headers, json={"scope_type": "material", "material_id": material.id, "question": "总结"})

    assert response.status_code == 400


def test_chat_omitted_scope_type_preserves_legacy_all_behavior(client, auth_headers, make_material):
    headers, user = auth_headers()
    make_material(user, status="ready")

    with patch("routes.chat.RAGService") as fake_rag:
        fake_rag.return_value.answer.return_value = ("旧行为回答", [])
        response = client.post("/api/chat", headers=headers, json={"question": "总结全部"})

    assert response.status_code == 200
    assert response.get_json()["answer"] == "旧行为回答"


def test_chat_references_are_normalized_in_history(app, make_user, make_chat):
    user = make_user()
    references = [{"type": "text", "material_title": "讲义", "content_preview": "a" * 301}]
    row = make_chat(user, references_json=json.dumps(references, ensure_ascii=False))

    data = row.to_dict()

    assert data["references"][0]["material_title"] == "讲义"


def test_dashboard_stats_adds_enhanced_fields(client, auth_headers, make_material, make_task, make_chat):
    headers, user = auth_headers()
    make_material(user, title="失败资料", status="failed")
    make_material(user, title="未分类资料", status="ready")
    make_task(user, title="逾期任务", due_date=date.today() - timedelta(days=1), status="todo")
    make_task(user, title="今日任务", due_date=date.today(), status="todo")
    make_chat(user, question="最近问题", answer="最近答案")

    response = client.get("/api/stats/dashboard", headers=headers)

    assert response.status_code == 200
    data = response.get_json()
    assert "today_focus" in data
    assert data["today_focus"]["type"] == "overdue_task"
    assert data["next_actions"][0]["priority"] == 100
    assert "knowledge_health" in data
    assert "active_plan_summary" in data
    assert "ai_continuity" in data
    assert "recent_chats" in data
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
Set-Location "D:\学习资料\大数据综合实践\zonghexitong\backend"
python -m pytest tests\test_chat_stats_api.py -q
```

Expected: FAIL because `scope_type` and enhanced dashboard fields are missing.

- [ ] **Step 3: Add explicit scope handling to chat route**

Modify `backend/routes/chat.py` inside `chat()`.

After `folder_id = data.get("folder_id")`, add:

```python
    scope_type = (data.get("scope_type") or "").strip()
```

Before calling `RAGService`, add:

```python
        material_id = int(material_id) if material_id else None
        folder_id = int(folder_id) if folder_id else None
        if not scope_type:
            if material_id:
                scope_type = "material"
            elif folder_id:
                scope_type = "folder"
            else:
                scope_type = "all"
        if scope_type not in {"general", "all", "folder", "material"}:
            return jsonify({"message": "问答范围参数无效"}), 400
```

Use this branch:

```python
        if scope_type == "general":
            answer = AIService().answer(question, context="", conversation=_clean_conversation(conversation))
            references = []
        else:
            answer, references = RAGService().answer(
                user_id=user_id,
                question=question,
                scope_type=scope_type,
                material_id=material_id,
                folder_id=folder_id,
                conversation=_clean_conversation(conversation),
            )
```

Keep `ChatHistory` persistence unchanged except references are empty for general.

- [ ] **Step 4: Update RAGService answer signature and validations**

In `backend/services/rag_service.py`, update `answer()` to accept `scope_type=None` and apply these rules before retrieval:

```python
        scope_type = scope_type or ("material" if material_id else "folder" if folder_id else "all")
        if scope_type == "material":
            material = Material.query.filter_by(id=material_id, user_id=user_id).first()
            if not material:
                raise ValueError("资料不存在")
            if material.status != "ready":
                raise ValueError("该资料尚未处理完成，暂不能用于问答")
        elif scope_type == "folder":
            folder = MaterialFolder.query.filter_by(id=folder_id, user_id=user_id).first()
            if not folder:
                raise ValueError("文件夹不存在")
            ready_count = Material.query.filter_by(user_id=user_id, folder_id=folder_id, status="ready").count()
            if ready_count == 0:
                raise ValueError("该文件夹暂无可问答的资料")
        elif scope_type == "all":
            ready_count = Material.query.filter_by(user_id=user_id, status="ready").count()
            if ready_count == 0:
                raise ValueError("当前暂无可问答的资料，请先上传并处理资料，或切换为通用问答")
```

If imports are missing, add:

```python
from models.material import Material, MaterialFolder
```

- [ ] **Step 5: Normalize references while preserving legacy keys**

In `backend/services/rag_service.py`, replace `references_to_json()` with a version that returns normalized dictionaries and keeps legacy `title`/`content` keys:

```python
def references_to_json(references):
    normalized = []
    for item in references or []:
        ref_type = item.get("type") or "text"
        material_title = item.get("material_title") or item.get("title") or ""
        content_preview = (item.get("content_preview") or item.get("content") or item.get("snippet") or "")[:300]
        normalized.append(
            {
                "type": "visual" if ref_type == "image" else ref_type,
                "legacy_type": ref_type,
                "material_id": item.get("material_id"),
                "material_title": material_title,
                "folder_id": item.get("folder_id"),
                "folder_name": item.get("folder_name") or item.get("folder") or "",
                "chunk_id": item.get("chunk_id"),
                "chunk_index": item.get("chunk_index"),
                "asset_id": item.get("asset_id"),
                "asset_index": item.get("asset_index"),
                "page_number": item.get("page_number"),
                "caption": item.get("caption"),
                "content_preview": content_preview,
                "score": item.get("score"),
                "title": material_title,
                "content": content_preview,
            }
        )
    return json.dumps(normalized, ensure_ascii=False)
```

If `json` is not imported in that file, import it.

- [ ] **Step 6: Enhance dashboard stats**

Modify `backend/services/stats_service.py` `dashboard_stats()` to add enhanced fields while preserving existing fields:

```python
    base = {
        "total_materials": total_materials,
        "total_chats": total_chats,
        "total_tasks": total_tasks,
        "done_tasks": done_tasks,
        "today_tasks": len(today_tasks),
        "today_done_tasks": len([task for task in today_tasks if task.status == "done"]),
        "completion_rate": completion_rate,
        "recent_chats": [chat.to_dict() for chat in recent_chats],
        "weak_points": weak_points(user_id),
    }
    base["knowledge_health"] = knowledge_health(user_id)
    base["active_plan_summary"] = active_plan_summary(user_id)
    actions = next_actions(user_id, recent_chats)
    base["today_focus"] = actions[0] if actions else None
    base["next_actions"] = actions[:5]
    base["ai_continuity"] = {
        "recent_item": recent_chats[0].to_dict() if recent_chats else None,
        "route": "/chat" if recent_chats else "/chat?scope_type=all",
    }
    return base
```

Add these helper functions:

```python
def knowledge_health(user_id):
    materials = Material.query.filter_by(user_id=user_id).all()
    return {
        "total": len(materials),
        "ready": len([item for item in materials if item.status == "ready"]),
        "processing": len([item for item in materials if item.status == "processing"]),
        "failed": len([item for item in materials if item.status == "failed"]),
        "uncategorized": len([item for item in materials if not item.folder_id]),
        "visual_asset_count": sum(len(item.visual_assets) for item in materials),
    }


def active_plan_summary(user_id):
    tasks = StudyTask.query.filter_by(user_id=user_id).all()
    unfinished = [task for task in tasks if task.status != "done"]
    next_due = sorted([task for task in unfinished if task.due_date], key=lambda task: task.due_date)
    total = len(tasks)
    done = len([task for task in tasks if task.status == "done"])
    return {
        "active_count": len(set(task.plan_id for task in unfinished if task.plan_id)),
        "average_progress_percent": round(done / total * 100) if total else 0,
        "next_due_task": next_due[0].to_dict() if next_due else None,
    }


def _action(type_, title, reason, priority, route, action_label):
    return {"type": type_, "title": title, "reason": reason, "priority": priority, "route": route, "action_label": action_label}


def next_actions(user_id, recent_chats):
    today = date.today()
    actions = []
    overdue = StudyTask.query.filter(StudyTask.user_id == user_id, StudyTask.status == "todo", StudyTask.due_date < today).order_by(StudyTask.due_date.asc()).limit(3).all()
    actions.extend([_action("overdue_task", task.title, "已逾期", 100, "/plans?task_scope=overdue", "处理逾期任务") for task in overdue])
    due_today = StudyTask.query.filter_by(user_id=user_id, status="todo", due_date=today).limit(3).all()
    actions.extend([_action("due_today", task.title, "今天截止", 90, "/plans?task_scope=today", "完成今日任务") for task in due_today])
    failed = Material.query.filter_by(user_id=user_id, status="failed").limit(2).all()
    actions.extend([_action("failed_material", item.title, "资料处理失败", 80, f"/materials/{item.id}", "查看失败原因") for item in failed])
    uncategorized = Material.query.filter_by(user_id=user_id, folder_id=None).limit(2).all()
    actions.extend([_action("unclassified_material", item.title, "尚未分类", 70, "/materials", "整理知识库") for item in uncategorized])
    actions.extend([_action("recent_chat", chat.question, "继续最近问答", 60, "/chat", "继续追问") for chat in recent_chats[:2]])
    ready = Material.query.filter_by(user_id=user_id, status="ready").order_by(Material.created_at.desc()).limit(2).all()
    actions.extend([_action("ready_new_material", item.title, "可开始资料问答", 50, f"/chat?scope_type=material&material_id={item.id}", "基于资料提问") for item in ready])
    if not actions:
        actions.append(_action("empty_start", "上传第一份学习资料", "开始建立个人知识库", 40, "/materials?upload=1", "上传资料"))
    actions.sort(key=lambda item: item["priority"], reverse=True)
    return actions
```

- [ ] **Step 7: Run chat/stats tests**

Run:

```powershell
Set-Location "D:\学习资料\大数据综合实践\zonghexitong\backend"
python -m pytest tests\test_chat_stats_api.py -q
```

Expected: PASS.

- [ ] **Step 8: Commit chat and stats backend work**

Run:

```powershell
git add backend/tests/test_chat_stats_api.py backend/routes/chat.py backend/services/rag_service.py backend/models/chat.py backend/services/stats_service.py
git commit -m @'
feat: add scoped chat and dashboard stats

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
'@
```

---

## Task 6: Backend regression checkpoint

**Files:**
- No planned source changes unless tests fail.

- [ ] **Step 1: Run material tests**

Run:

```powershell
Set-Location "D:\学习资料\大数据综合实践\zonghexitong\backend"
python -m pytest tests\test_materials_api.py -q
```

Expected: PASS.

- [ ] **Step 2: Run plan/task tests**

Run:

```powershell
Set-Location "D:\学习资料\大数据综合实践\zonghexitong\backend"
python -m pytest tests\test_tasks_plans_api.py -q
```

Expected: PASS.

- [ ] **Step 3: Run chat/stats tests**

Run:

```powershell
Set-Location "D:\学习资料\大数据综合实践\zonghexitong\backend"
python -m pytest tests\test_chat_stats_api.py -q
```

Expected: PASS.

- [ ] **Step 4: Run full backend suite and compile check**

Run:

```powershell
Set-Location "D:\学习资料\大数据综合实践\zonghexitong\backend"
python -m pytest tests -q
python -m compileall "D:\学习资料\大数据综合实践\zonghexitong\backend"
```

Expected: all tests pass and compileall reports no syntax errors.

- [ ] **Step 5: Commit only if fixes were needed**

If this checkpoint required code changes, commit them with:

```powershell
git add backend
git commit -m @'
fix: stabilize backend redesign contracts

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
'@
```

If no changes were needed, do not commit.

---

## Task 7: Frontend API wrappers and shared UI foundation

**Files:**
- Modify: `frontend/src/api/modules.js`
- Create: `frontend/src/components/study/PageHeader.vue`
- Create: `frontend/src/components/study/WorkbenchPanel.vue`
- Create: `frontend/src/components/study/MetricCard.vue`
- Create: `frontend/src/components/study/StatusBadge.vue`
- Create: `frontend/src/components/study/EmptyGuide.vue`
- Modify: `frontend/src/styles.css`

- [ ] **Step 1: Add frontend API methods**

Modify `frontend/src/api/modules.js`:

```js
export const chatApi = {
  ask: (data) => http.post('/chat', data),
  history: () => http.get('/chat/history'),
  conversations: (params = {}) => http.get('/chat/conversations', { params }),
  createConversation: (data) => http.post('/chat/conversations', data),
  messages: (id) => http.get(`/chat/conversations/${id}/messages`),
  sendMessage: (id, data) => http.post(`/chat/conversations/${id}/messages`, data)
}

export const planApi = {
  list: (params = {}) => http.get('/plans', { params }),
  create: (data) => http.post('/plans', data),
  update: (id, data) => http.put(`/plans/${id}`, data),
  remove: (id) => http.delete(`/plans/${id}`),
  aiPreview: (data) => http.post('/plans/ai-preview', data),
  createFromPreview: (data) => http.post('/plans/from-preview', data)
}

export const taskApi = {
  list: (params = {}) => http.get('/tasks', { params }),
  today: () => http.get('/tasks/today'),
  create: (data) => http.post('/tasks', data),
  update: (id, data) => http.put(`/tasks/${id}`, data),
  remove: (id) => http.delete(`/tasks/${id}`),
  complete: (id) => http.post(`/tasks/${id}/complete`),
  undo: (id) => http.post(`/tasks/${id}/undo`)
}
```

Keep `materialApi.assetImage` unchanged with `responseType: 'blob'`.

- [ ] **Step 2: Create PageHeader component**

Create `frontend/src/components/study/PageHeader.vue`:

```vue
<template>
  <div class="page-heading study-page-header">
    <div>
      <p v-if="kicker" class="page-kicker">{{ kicker }}</p>
      <h1 class="page-title">{{ title }}</h1>
      <p v-if="subtitle" class="page-subtitle">{{ subtitle }}</p>
    </div>
    <div v-if="$slots.actions" class="toolbar-actions">
      <slot name="actions" />
    </div>
  </div>
</template>

<script setup>
defineProps({
  kicker: { type: String, default: '' },
  title: { type: String, required: true },
  subtitle: { type: String, default: '' }
})
</script>
```

- [ ] **Step 3: Create WorkbenchPanel component**

Create `frontend/src/components/study/WorkbenchPanel.vue`:

```vue
<template>
  <section :class="['panel', 'workbench-panel', accent ? `accent-${accent}` : '']">
    <div v-if="title || subtitle || $slots.actions" class="toolbar">
      <div>
        <h3 v-if="title" class="panel-title">{{ title }}</h3>
        <p v-if="subtitle" class="panel-subtitle">{{ subtitle }}</p>
      </div>
      <div v-if="$slots.actions" class="toolbar-actions">
        <slot name="actions" />
      </div>
    </div>
    <slot />
  </section>
</template>

<script setup>
defineProps({
  title: { type: String, default: '' },
  subtitle: { type: String, default: '' },
  accent: { type: String, default: '' }
})
</script>
```

- [ ] **Step 4: Create MetricCard component**

Create `frontend/src/components/study/MetricCard.vue`:

```vue
<template>
  <div class="panel stat-card metric-card">
    <div class="stat-head">
      <div class="stat-label">{{ label }}</div>
      <div class="stat-icon">{{ icon }}</div>
    </div>
    <div class="stat-value">{{ value }}</div>
    <p v-if="hint" class="panel-subtitle">{{ hint }}</p>
  </div>
</template>

<script setup>
defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number], required: true },
  icon: { type: String, default: '•' },
  hint: { type: String, default: '' }
})
</script>
```

- [ ] **Step 5: Create StatusBadge component**

Create `frontend/src/components/study/StatusBadge.vue`:

```vue
<template>
  <el-tag :type="tagType" :size="size">{{ label }}</el-tag>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  code: { type: String, default: 'unknown' },
  size: { type: String, default: 'small' }
})

const STATUS_MAP = {
  ready: { label: '已可提问', type: 'success' },
  processing: { label: '处理中', type: 'warning' },
  failed: { label: '处理失败', type: 'danger' },
  todo: { label: '待完成', type: 'info' },
  done: { label: '已完成', type: 'success' },
  overdue: { label: '已逾期', type: 'danger' },
  not_started: { label: '未开始', type: 'info' },
  active: { label: '进行中', type: '' },
  empty: { label: '暂无任务', type: 'info' },
  unknown: { label: '状态未知', type: 'info' }
}

const current = computed(() => STATUS_MAP[props.code] || STATUS_MAP.unknown)
const label = computed(() => current.value.label)
const tagType = computed(() => current.value.type)
</script>
```

- [ ] **Step 6: Create EmptyGuide component**

Create `frontend/src/components/study/EmptyGuide.vue`:

```vue
<template>
  <div class="empty-guide">
    <div class="empty-guide-icon">{{ icon }}</div>
    <h3>{{ title }}</h3>
    <p>{{ description }}</p>
    <slot name="action" />
  </div>
</template>

<script setup>
defineProps({
  icon: { type: String, default: '学' },
  title: { type: String, required: true },
  description: { type: String, required: true }
})
</script>
```

- [ ] **Step 7: Add shared workbench styles**

Append to `frontend/src/styles.css`:

```css
.study-page-header {
  align-items: flex-start;
}

.workbench-panel {
  position: relative;
  overflow: hidden;
}

.workbench-panel.accent-ai::before,
.workbench-panel.accent-primary::before,
.workbench-panel.accent-warning::before {
  content: '';
  position: absolute;
  inset: 0 auto 0 0;
  width: 5px;
  background: var(--color-primary);
}

.workbench-panel.accent-ai::before { background: #8b7cf6; }
.workbench-panel.accent-warning::before { background: var(--color-yellow); }

.empty-guide {
  padding: 28px;
  border: 1px dashed rgba(47, 128, 237, 0.28);
  border-radius: 24px;
  text-align: center;
  background: rgba(255, 255, 255, 0.58);
}

.empty-guide-icon {
  display: inline-grid;
  place-items: center;
  width: 52px;
  height: 52px;
  margin-bottom: 10px;
  border-radius: 18px;
  background: rgba(47, 128, 237, 0.12);
  color: var(--color-primary);
  font-weight: 800;
}

.metric-card {
  min-height: 136px;
}

.action-list {
  display: grid;
  gap: 10px;
}

.action-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  width: 100%;
  padding: 14px 16px;
  border: 1px solid rgba(47, 128, 237, 0.14);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.72);
  text-align: left;
}

.action-card:focus-visible,
.history-item:focus-visible,
.folder-row:focus-visible,
.folder-row-main:focus-visible {
  outline: 3px solid rgba(47, 128, 237, 0.32);
  outline-offset: 2px;
}

@media (max-width: 768px) {
  .study-page-header {
    gap: 16px;
  }

  .study-page-header .toolbar-actions {
    width: 100%;
    justify-content: flex-start;
  }
}
```

- [ ] **Step 8: Run frontend build**

Run:

```powershell
Set-Location "D:\学习资料\大数据综合实践\zonghexitong\frontend"
npm run build
```

Expected: Vite build completes without import or template errors.

- [ ] **Step 9: Commit frontend foundation**

Run:

```powershell
git add frontend/src/api/modules.js frontend/src/components/study frontend/src/styles.css
git commit -m @'
feat: add study workbench ui foundation

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
'@
```

---

## Task 8: AppLayout and Profile IA/preferences

**Files:**
- Modify: `frontend/src/components/AppLayout.vue`
- Modify: `frontend/src/views/Profile.vue`

- [ ] **Step 1: Update AppLayout navigation labels without changing routes**

In `frontend/src/components/AppLayout.vue`, ensure the nav array uses:

```js
const navItems = [
  { path: '/dashboard', label: '今日驾驶舱', icon: '今' },
  { path: '/materials', label: '知识库', icon: '库' },
  { path: '/chat', label: 'AI 学习会话', icon: '问' },
  { path: '/plans', label: '学习计划', icon: '划' },
  { path: '/profile', label: '个人设置', icon: '我' }
]
```

If the file uses a different nav data shape, preserve the shape and change only label/icon/path values.

- [ ] **Step 2: Surface the study goal in the topbar**

In `AppLayout.vue`, add a topbar text element that reads from the auth user:

```vue
<p class="topbar-goal">
  {{ auth.user?.study_goal || '设置一个学习目标，让系统更懂你的计划。' }}
</p>
```

Do not remove the skip link or logout action.

- [ ] **Step 3: Add Profile local preference state**

In `frontend/src/views/Profile.vue`, add local preference refs:

```js
const defaultScope = ref(localStorage.getItem('studyhub.defaultScope') || 'all')
const answerStyle = ref(localStorage.getItem('studyhub.answerStyle') || 'step_by_step')
const evidenceExpanded = ref(localStorage.getItem('studyhub.evidenceExpanded') === 'true')
const defaultTaskMinutes = ref(Number(localStorage.getItem('studyhub.defaultTaskMinutes') || 30))

function saveLocalPreferences() {
  localStorage.setItem('studyhub.defaultScope', defaultScope.value)
  localStorage.setItem('studyhub.answerStyle', answerStyle.value)
  localStorage.setItem('studyhub.evidenceExpanded', String(evidenceExpanded.value))
  localStorage.setItem('studyhub.defaultTaskMinutes', String(defaultTaskMinutes.value || 30))
  ElMessage.success('学习偏好已保存')
}
```

- [ ] **Step 4: Add Profile preference controls**

Add a panel to `Profile.vue` template:

```vue
<div class="panel section-gap">
  <h3 class="panel-title">学习偏好</h3>
  <p class="panel-subtitle">这些偏好先保存在本地浏览器，用于当前学习工作台体验。</p>
  <el-form label-position="top">
    <el-form-item label="默认问答范围">
      <el-select v-model="defaultScope" class="full-width">
        <el-option label="全部资料" value="all" />
        <el-option label="通用问答" value="general" />
      </el-select>
    </el-form-item>
    <el-form-item label="回答风格">
      <el-select v-model="answerStyle" class="full-width">
        <el-option label="分步骤解释" value="step_by_step" />
        <el-option label="简洁总结" value="concise" />
        <el-option label="考试复习重点" value="exam_review" />
      </el-select>
    </el-form-item>
    <el-form-item label="默认展开证据">
      <el-switch v-model="evidenceExpanded" />
    </el-form-item>
    <el-form-item label="默认任务时长（分钟）">
      <el-input-number v-model="defaultTaskMinutes" :min="10" :max="480" />
    </el-form-item>
    <el-button type="primary" @click="saveLocalPreferences">保存学习偏好</el-button>
  </el-form>
</div>

<div class="panel section-gap">
  <h3 class="panel-title">数据与 AI 说明</h3>
  <p class="panel-subtitle">上传资料仅用于当前账号的知识库检索和个人学习问答。AI 回答会标注可用引用，通用问答不会伪装成资料证据。</p>
</div>
```

- [ ] **Step 5: Run frontend build**

Run:

```powershell
Set-Location "D:\学习资料\大数据综合实践\zonghexitong\frontend"
npm run build
```

Expected: PASS.

- [ ] **Step 6: Commit AppLayout/Profile changes**

Run:

```powershell
git add frontend/src/components/AppLayout.vue frontend/src/views/Profile.vue
git commit -m @'
feat: update app shell and study preferences

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
'@
```

---

## Task 9: Dashboard redesign

**Files:**
- Modify: `frontend/src/views/Dashboard.vue`

- [ ] **Step 1: Add shared imports**

In `Dashboard.vue`, add:

```js
import PageHeader from '../components/study/PageHeader.vue'
import WorkbenchPanel from '../components/study/WorkbenchPanel.vue'
import MetricCard from '../components/study/MetricCard.vue'
import EmptyGuide from '../components/study/EmptyGuide.vue'
```

Keep ECharts imports and chart lifecycle functions.

- [ ] **Step 2: Add safe fallback computed values**

Add these computed values:

```js
const knowledgeHealth = computed(() => stats.value.knowledge_health || {
  total: stats.value.total_materials || 0,
  ready: 0,
  processing: 0,
  failed: 0,
  uncategorized: 0,
  visual_asset_count: 0
})

const todayFocus = computed(() => stats.value.today_focus || fallbackActions.value[0] || null)
const nextActions = computed(() => (stats.value.next_actions?.length ? stats.value.next_actions : fallbackActions.value).slice(0, 5))
const aiContinuity = computed(() => stats.value.ai_continuity || {
  recent_item: stats.value.recent_chats?.[0] || null,
  route: '/chat'
})

const fallbackActions = computed(() => {
  const actions = []
  if ((stats.value.today_tasks || 0) > (stats.value.today_done_tasks || 0)) {
    actions.push({ type: 'due_today', title: '完成今日剩余任务', reason: '今天还有任务未完成', priority: 90, route: '/plans?task_scope=today', action_label: '查看今日任务' })
  }
  if (stats.value.recent_chats?.[0]) {
    actions.push({ type: 'recent_chat', title: stats.value.recent_chats[0].question, reason: '继续最近问答', priority: 60, route: '/chat', action_label: '继续追问' })
  }
  if (!actions.length) {
    actions.push({ type: 'empty_start', title: '上传第一份学习资料', reason: '开始建立个人知识库', priority: 40, route: '/materials?upload=1', action_label: '上传资料' })
  }
  return actions.sort((a, b) => b.priority - a.priority)
})
```

- [ ] **Step 3: Replace the page header template**

Replace the current `.page-heading` with:

```vue
<PageHeader
  kicker="Today Learning Cockpit"
  title="今日驾驶舱"
  subtitle="先看今天要做什么，再决定从资料、AI 问答还是计划继续。"
>
  <template #actions>
    <el-button :icon="Refresh" :loading="loading" @click="load">刷新数据</el-button>
  </template>
</PageHeader>
```

- [ ] **Step 4: Add Today Focus and next actions above charts**

Add after header:

```vue
<div class="grid two-col">
  <WorkbenchPanel title="今日学习焦点" subtitle="系统根据任务、资料和最近问答给出优先行动。" accent="primary">
    <EmptyGuide v-if="!todayFocus" title="今天还没有学习焦点" description="上传资料或创建任务后，这里会给出下一步建议。">
      <template #action>
        <el-button type="primary" @click="$router.push('/materials?upload=1')">上传资料</el-button>
      </template>
    </EmptyGuide>
    <div v-else class="hero-focus-card">
      <el-tag size="large">{{ todayFocus.reason }}</el-tag>
      <h2>{{ todayFocus.title }}</h2>
      <el-button type="primary" @click="$router.push(todayFocus.route)">{{ todayFocus.action_label }}</el-button>
    </div>
  </WorkbenchPanel>

  <WorkbenchPanel title="推荐下一步" subtitle="最多展示 5 个可执行学习动作。" accent="ai">
    <div class="action-list">
      <button v-for="action in nextActions" :key="`${action.type}-${action.title}`" type="button" class="action-card" @click="$router.push(action.route)">
        <span>
          <strong>{{ action.title }}</strong>
          <p class="muted">{{ action.reason }}</p>
        </span>
        <el-tag>{{ action.action_label }}</el-tag>
      </button>
    </div>
  </WorkbenchPanel>
</div>
```

- [ ] **Step 5: Replace stat card markup with MetricCard**

Use:

```vue
<div class="grid stats-grid section-gap">
  <MetricCard v-for="card in statCards" :key="card.label" :label="card.label" :value="card.value" :icon="card.icon" :hint="card.hint" />
</div>
```

- [ ] **Step 6: Add knowledge health and AI continuity panels**

Add before recent chats:

```vue
<div class="grid two-col section-gap">
  <WorkbenchPanel title="知识库健康度" subtitle="资料是否已经处理完成，决定 AI 能否引用它们。">
    <el-space wrap>
      <el-tag type="success">可问答 {{ knowledgeHealth.ready }}</el-tag>
      <el-tag type="warning">处理中 {{ knowledgeHealth.processing }}</el-tag>
      <el-tag type="danger">失败 {{ knowledgeHealth.failed }}</el-tag>
      <el-tag type="info">未分类 {{ knowledgeHealth.uncategorized }}</el-tag>
      <el-tag>视觉资产 {{ knowledgeHealth.visual_asset_count }}</el-tag>
    </el-space>
  </WorkbenchPanel>

  <WorkbenchPanel title="AI 学习连续性" subtitle="从最近一次问答继续学习。">
    <EmptyGuide v-if="!aiContinuity.recent_item" title="还没有问答记录" description="选择资料或直接进入通用问答，开始第一次学习会话。">
      <template #action>
        <el-button type="primary" @click="$router.push('/chat?scope_type=all')">开始提问</el-button>
      </template>
    </EmptyGuide>
    <button v-else type="button" class="action-card" @click="$router.push(aiContinuity.route)">
      <span>
        <strong>{{ aiContinuity.recent_item.question }}</strong>
        <p class="muted">{{ aiContinuity.recent_item.answer?.slice(0, 90) }}</p>
      </span>
      <el-tag>继续</el-tag>
    </button>
  </WorkbenchPanel>
</div>
```

- [ ] **Step 7: Run frontend build**

Run:

```powershell
Set-Location "D:\学习资料\大数据综合实践\zonghexitong\frontend"
npm run build
```

Expected: PASS.

- [ ] **Step 8: Commit dashboard redesign**

Run:

```powershell
git add frontend/src/views/Dashboard.vue
git commit -m @'
feat: redesign learning dashboard

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
'@
```

---

## Task 10: Knowledge Library components and Materials page

**Files:**
- Create: `frontend/src/components/study/MaterialCard.vue`
- Create: `frontend/src/components/study/FolderShelf.vue`
- Create: `frontend/src/components/study/MaterialFilters.vue`
- Create: `frontend/src/components/study/UploadMaterialDialog.vue`
- Modify: `frontend/src/views/Materials.vue`
- Modify: `frontend/src/styles.css`

- [ ] **Step 1: Create MaterialCard component**

Create `frontend/src/components/study/MaterialCard.vue`:

```vue
<template>
  <article class="material-card">
    <div class="material-card-head">
      <el-tag>{{ material.file_type?.toUpperCase() || 'FILE' }}</el-tag>
      <StatusBadge :code="material.status" />
    </div>
    <h3>{{ material.title }}</h3>
    <p class="muted">{{ material.folder_name || '未分类' }}</p>
    <p class="material-summary">{{ material.summary || material.error_message || '暂无摘要' }}</p>
    <div class="keyword-list">
      <el-tag v-for="keyword in visibleKeywords" :key="keyword">{{ keyword }}</el-tag>
      <span v-if="extraKeywordCount" class="muted">+{{ extraKeywordCount }}</span>
    </div>
    <div class="material-meta-row">
      <span>切片 {{ material.chunk_count || 0 }}</span>
      <span>视觉资产 {{ material.visual_asset_count || 0 }}</span>
    </div>
    <div class="material-card-actions">
      <el-button @click="$emit('view', material)">查看详情</el-button>
      <el-button type="primary" :disabled="material.status !== 'ready'" @click="$emit('ask', material)">
        {{ material.status === 'ready' ? '向 AI 提问' : '暂不可问答' }}
      </el-button>
      <el-dropdown trigger="click" @command="(command) => $emit(command, material)">
        <el-button>更多</el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="reindex">重建索引</el-dropdown-item>
            <el-dropdown-item command="remove">删除</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </article>
</template>

<script setup>
import { computed } from 'vue'
import StatusBadge from './StatusBadge.vue'

const props = defineProps({ material: { type: Object, required: true } })
defineEmits(['view', 'ask', 'reindex', 'remove'])

const visibleKeywords = computed(() => (props.material.keywords || []).slice(0, 4))
const extraKeywordCount = computed(() => Math.max((props.material.keywords || []).length - 4, 0))
</script>
```

- [ ] **Step 2: Create FolderShelf component**

Create `frontend/src/components/study/FolderShelf.vue`:

```vue
<template>
  <div class="folder-list section-gap">
    <button type="button" :class="['folder-row', selected === null ? 'active' : '']" @click="$emit('select', null)">
      <span>全部资料</span>
      <el-tag size="small">{{ totalCount }}</el-tag>
    </button>
    <button type="button" :class="['folder-row', selected === 'uncategorized' ? 'active' : '']" @click="$emit('select', 'uncategorized')">
      <span>未分类</span>
      <el-tag size="small" type="info">{{ uncategorizedCount }}</el-tag>
    </button>
    <div v-for="folder in folders" :key="folder.id" :class="['folder-row', selected === folder.id ? 'active' : '']">
      <button type="button" class="folder-row-main" @click="$emit('select', folder.id)">
        <strong>{{ folder.name }}</strong>
        <span class="folder-counts">{{ folder.material_count || 0 }} 份 · 可问答 {{ folder.ready_count || 0 }}</span>
      </button>
      <el-dropdown trigger="click" @command="(command) => $emit(command, folder)">
        <el-button text aria-label="文件夹更多操作">⋯</el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="edit">重命名</el-dropdown-item>
            <el-dropdown-item command="delete">删除</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </div>
</template>

<script setup>
defineProps({
  folders: { type: Array, default: () => [] },
  selected: { type: [Number, String, null], default: null },
  totalCount: { type: Number, default: 0 },
  uncategorizedCount: { type: Number, default: 0 }
})
defineEmits(['select', 'edit', 'delete'])
</script>
```

- [ ] **Step 3: Create MaterialFilters component**

Create `frontend/src/components/study/MaterialFilters.vue`:

```vue
<template>
  <div class="material-filters">
    <el-input :model-value="q" placeholder="搜索标题、关键词、摘要" clearable @update:model-value="$emit('update:q', $event)" />
    <el-select :model-value="status" clearable placeholder="状态" @update:model-value="$emit('update:status', $event)">
      <el-option label="已可提问" value="ready" />
      <el-option label="处理中" value="processing" />
      <el-option label="处理失败" value="failed" />
    </el-select>
    <el-select :model-value="fileType" clearable placeholder="类型" @update:model-value="$emit('update:fileType', $event)">
      <el-option v-for="type in fileTypes" :key="type" :label="type.toUpperCase()" :value="type" />
    </el-select>
    <el-select :model-value="sort" placeholder="排序" @update:model-value="$emit('update:sort', $event)">
      <el-option label="最新上传" value="created_desc" />
      <el-option label="标题 A-Z" value="title_asc" />
      <el-option label="状态优先" value="status" />
      <el-option label="资料丰富度" value="richness_desc" />
    </el-select>
    <el-segmented :model-value="viewMode" :options="viewOptions" @update:model-value="$emit('update:viewMode', $event)" />
  </div>
</template>

<script setup>
defineProps({
  q: { type: String, default: '' },
  status: { type: String, default: '' },
  fileType: { type: String, default: '' },
  sort: { type: String, default: 'created_desc' },
  viewMode: { type: String, default: 'cards' },
  fileTypes: { type: Array, default: () => [] }
})
defineEmits(['update:q', 'update:status', 'update:fileType', 'update:sort', 'update:viewMode'])
const viewOptions = [{ label: '资料库', value: 'cards' }, { label: '管理表格', value: 'table' }]
</script>
```

- [ ] **Step 4: Refactor Materials page state**

In `Materials.vue`, ensure state includes:

```js
const viewMode = ref(localStorage.getItem('studyhub.materialViewMode') || 'cards')
const q = ref(String(route.query.q || ''))
const statusFilter = ref(String(route.query.status || ''))
const fileTypeFilter = ref('')
const sortKey = ref('created_desc')
```

Add computed `visibleMaterials`:

```js
const visibleMaterials = computed(() => {
  let rows = [...allMaterials.value]
  if (selectedFolderId.value === 'uncategorized') rows = rows.filter((item) => !item.folder_id)
  if (typeof selectedFolderId.value === 'number') rows = rows.filter((item) => item.folder_id === selectedFolderId.value)
  const needle = q.value.trim().toLowerCase()
  if (needle) {
    rows = rows.filter((item) => [item.title, item.file_name, item.folder_name, item.summary, ...(item.keywords || [])].join(' ').toLowerCase().includes(needle))
  }
  if (statusFilter.value) rows = rows.filter((item) => item.status === statusFilter.value)
  if (fileTypeFilter.value) rows = rows.filter((item) => item.file_type === fileTypeFilter.value)
  const richness = (item) => (item.chunk_count || 0) + (item.visual_asset_count || 0) * 3 + Math.min((item.keywords || []).length, 5)
  rows.sort((a, b) => {
    if (sortKey.value === 'title_asc') return a.title.localeCompare(b.title, 'zh-CN')
    if (sortKey.value === 'status') return (a.status || '').localeCompare(b.status || '')
    if (sortKey.value === 'richness_desc') return richness(b) - richness(a)
    return new Date(b.updated_at || b.created_at || 0) - new Date(a.updated_at || a.created_at || 0)
  })
  return rows
})
```

Update table/card rendering to use `visibleMaterials`.

- [ ] **Step 5: Add card mode and keep table mode**

In `Materials.vue` main panel, render:

```vue
<MaterialFilters
  v-model:q="q"
  v-model:status="statusFilter"
  v-model:file-type="fileTypeFilter"
  v-model:sort="sortKey"
  v-model:view-mode="viewMode"
  :file-types="fileTypes"
/>

<div v-if="viewMode === 'cards'" class="material-card-grid section-gap">
  <MaterialCard
    v-for="material in visibleMaterials"
    :key="material.id"
    :material="material"
    @view="goDetail"
    @ask="goAsk"
    @reindex="reindex"
    @remove="remove"
  />
</div>
<div v-else class="table-wrap section-gap">
  <el-table :data="visibleMaterials" v-loading="loading">
    <!-- keep existing useful columns, use visibleMaterials -->
  </el-table>
</div>
```

Add methods:

```js
function goDetail(material) {
  router.push(`/materials/${material.id}`)
}

function goAsk(material) {
  if (material.status !== 'ready') return
  router.push(`/chat?scope_type=material&material_id=${material.id}`)
}

async function reindex(material) {
  await materialApi.reindex(material.id)
  ElMessage.success('已重新建立索引')
  await load()
}
```

- [ ] **Step 6: Add Materials styles**

Append:

```css
.material-card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 16px;
}

.material-card {
  display: grid;
  gap: 10px;
  padding: 18px;
  border: 1px solid rgba(47, 128, 237, 0.12);
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.74);
  box-shadow: var(--shadow-soft);
}

.material-card-head,
.material-meta-row,
.material-card-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
}

.material-summary {
  min-height: 48px;
  color: var(--color-muted);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.material-filters {
  display: grid;
  grid-template-columns: minmax(220px, 1.5fr) repeat(3, minmax(130px, 1fr)) auto;
  gap: 12px;
  align-items: center;
}

.folder-counts {
  display: block;
  margin-top: 3px;
  color: var(--color-muted);
  font-size: 12px;
}

@media (max-width: 900px) {
  .material-filters {
    grid-template-columns: 1fr;
  }
}
```

- [ ] **Step 7: Run frontend build**

Run:

```powershell
Set-Location "D:\学习资料\大数据综合实践\zonghexitong\frontend"
npm run build
```

Expected: PASS.

- [ ] **Step 8: Commit knowledge library redesign**

Run:

```powershell
git add frontend/src/components/study/MaterialCard.vue frontend/src/components/study/FolderShelf.vue frontend/src/components/study/MaterialFilters.vue frontend/src/components/study/UploadMaterialDialog.vue frontend/src/views/Materials.vue frontend/src/styles.css
git commit -m @'
feat: redesign knowledge library

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
'@
```

---

## Task 11: MaterialDetail knowledge object page

**Files:**
- Create: `frontend/src/components/study/VisualAssetGrid.vue`
- Modify: `frontend/src/views/MaterialDetail.vue`

- [ ] **Step 1: Create VisualAssetGrid component**

Create `frontend/src/components/study/VisualAssetGrid.vue`:

```vue
<template>
  <div class="visual-asset-grid">
    <article v-for="asset in assets" :key="asset.id" class="visual-asset-card">
      <div class="visual-preview">
        <img v-if="urls[asset.id]" :src="urls[asset.id]" :alt="asset.caption || `视觉资产 ${asset.asset_index + 1}`" />
        <span v-else>图片不可用</span>
      </div>
      <strong>{{ asset.caption || `视觉资产 ${asset.asset_index + 1}` }}</strong>
      <p class="muted">{{ asset.page_number ? `第 ${asset.page_number} 页` : '无页码' }}</p>
      <StatusBadge :code="asset.status" />
    </article>
  </div>
</template>

<script setup>
import { onBeforeUnmount, watch, ref } from 'vue'
import { materialApi } from '../../api/modules'
import StatusBadge from './StatusBadge.vue'

const props = defineProps({ assets: { type: Array, default: () => [] } })
const urls = ref({})

function revokeAll() {
  Object.values(urls.value).forEach((url) => URL.revokeObjectURL(url))
  urls.value = {}
}

async function loadImages() {
  revokeAll()
  const entries = await Promise.all(props.assets.map(async (asset) => {
    try {
      const blob = await materialApi.assetImage(asset.id)
      return [asset.id, URL.createObjectURL(blob)]
    } catch (error) {
      return null
    }
  }))
  urls.value = Object.fromEntries(entries.filter(Boolean))
}

watch(() => props.assets, loadImages, { immediate: true, deep: true })
onBeforeUnmount(revokeAll)
</script>
```

- [ ] **Step 2: Update MaterialDetail imports and health computed**

In `MaterialDetail.vue`, import:

```js
import PageHeader from '../components/study/PageHeader.vue'
import WorkbenchPanel from '../components/study/WorkbenchPanel.vue'
import StatusBadge from '../components/study/StatusBadge.vue'
import VisualAssetGrid from '../components/study/VisualAssetGrid.vue'
```

Add:

```js
const visualAssets = computed(() => material.value?.visual_assets || [])
const chunks = computed(() => material.value?.chunks || [])
const recommendedQuestions = computed(() => {
  const title = material.value?.title || '这份资料'
  const keywords = (material.value?.keywords || []).slice(0, 3)
  return [
    `请总结《${title}》的核心内容`,
    `列出《${title}》的考试重点`,
    ...keywords.map((keyword) => `请解释 ${keyword} 这个知识点`)
  ].slice(0, 5)
})

function askWithPrompt(prompt = '') {
  const query = new URLSearchParams({ scope_type: 'material', material_id: String(material.value.id) })
  if (prompt) query.set('prompt', prompt)
  router.push(`/chat?${query.toString()}`)
}
```

- [ ] **Step 3: Add page header and health panels**

Replace the header area with:

```vue
<PageHeader
  kicker="Knowledge Object"
  :title="material?.title || '资料详情'"
  :subtitle="material?.file_name || '查看资料摘要、视觉资产和文本片段。'"
>
  <template #actions>
    <StatusBadge :code="material?.status || 'unknown'" size="large" />
    <el-button @click="$router.push('/materials')">返回知识库</el-button>
    <el-button type="primary" :disabled="material?.status !== 'ready'" @click="askWithPrompt()">基于资料提问</el-button>
  </template>
</PageHeader>
```

Add health metrics:

```vue
<div class="grid stats-grid">
  <MetricCard label="文本切片" :value="material?.chunk_count || chunks.length" icon="文" hint="可被 AI 检索的文本片段" />
  <MetricCard label="视觉资产" :value="material?.visual_asset_count || visualAssets.length" icon="图" hint="图片、页面或图表证据" />
  <MetricCard label="可用视觉资产" :value="material?.ready_visual_asset_count || visualAssets.filter((item) => item.status === 'ready').length" icon="✓" hint="可作为视觉证据" />
  <MetricCard label="失败视觉资产" :value="material?.failed_visual_asset_count || visualAssets.filter((item) => item.status === 'failed').length" icon="!" hint="需要检查或重建索引" />
</div>
```

- [ ] **Step 4: Render visual assets and recommended questions**

Add:

```vue
<WorkbenchPanel title="推荐提问" subtitle="点击后只会预填问题，不会自动发送。" class="section-gap">
  <el-space wrap>
    <el-button v-for="prompt in recommendedQuestions" :key="prompt" @click="askWithPrompt(prompt)">{{ prompt }}</el-button>
  </el-space>
</WorkbenchPanel>

<WorkbenchPanel title="视觉资产" subtitle="系统从资料中提取的页面、图片或图表。" class="section-gap">
  <VisualAssetGrid v-if="visualAssets.length" :assets="visualAssets" />
  <el-empty v-else description="暂无视觉资产" />
</WorkbenchPanel>
```

- [ ] **Step 5: Add chunk search/copy behavior**

Add state:

```js
const chunkQuery = ref('')
const filteredChunks = computed(() => {
  const needle = chunkQuery.value.trim().toLowerCase()
  if (!needle) return chunks.value
  return chunks.value.filter((chunk) => chunk.content.toLowerCase().includes(needle))
})

async function copyChunk(chunk) {
  await navigator.clipboard.writeText(chunk.content)
  ElMessage.success('片段已复制')
}
```

Render chunks:

```vue
<WorkbenchPanel title="文本片段" subtitle="默认折叠显示，便于核对 AI 引用。" class="section-gap">
  <el-input v-model="chunkQuery" clearable placeholder="搜索片段内容" />
  <el-collapse class="section-gap">
    <el-collapse-item v-for="chunk in filteredChunks" :key="chunk.id" :title="`片段 ${chunk.chunk_index + 1}`">
      <p>{{ chunk.content }}</p>
      <el-button size="small" @click="copyChunk(chunk)">复制片段</el-button>
    </el-collapse-item>
  </el-collapse>
</WorkbenchPanel>
```

- [ ] **Step 6: Run frontend build**

Run:

```powershell
Set-Location "D:\学习资料\大数据综合实践\zonghexitong\frontend"
npm run build
```

Expected: PASS.

- [ ] **Step 7: Commit MaterialDetail redesign**

Run:

```powershell
git add frontend/src/components/study/VisualAssetGrid.vue frontend/src/views/MaterialDetail.vue
git commit -m @'
feat: redesign material detail

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
'@
```

---

## Task 12: Chat workbench redesign

**Files:**
- Create: `frontend/src/components/study/ScopeSelector.vue`
- Create: `frontend/src/components/study/EvidencePanel.vue`
- Create: `frontend/src/components/study/MessageBubble.vue`
- Modify: `frontend/src/views/Chat.vue`
- Modify: `frontend/src/styles.css`

- [ ] **Step 1: Create ScopeSelector component**

Create `frontend/src/components/study/ScopeSelector.vue`:

```vue
<template>
  <div class="scope-selector">
    <el-segmented :model-value="scopeType" :options="scopeOptions" @update:model-value="$emit('update:scopeType', $event)" />
    <el-select v-if="scopeType === 'folder'" :model-value="folderId" clearable placeholder="选择文件夹" class="full-width" @update:model-value="$emit('update:folderId', $event)">
      <el-option v-for="folder in folders" :key="folder.id" :label="folder.name" :value="folder.id" />
    </el-select>
    <el-select v-if="scopeType === 'material'" :model-value="materialId" clearable placeholder="选择资料" class="full-width" @update:model-value="$emit('update:materialId', $event)">
      <el-option v-for="material in readyMaterials" :key="material.id" :label="`${material.folder_name || '未分类'} / ${material.title}`" :value="material.id" />
    </el-select>
  </div>
</template>

<script setup>
import { computed } from 'vue'
const props = defineProps({
  scopeType: { type: String, default: 'all' },
  folderId: { type: [Number, null], default: null },
  materialId: { type: [Number, null], default: null },
  folders: { type: Array, default: () => [] },
  materials: { type: Array, default: () => [] }
})
defineEmits(['update:scopeType', 'update:folderId', 'update:materialId'])
const scopeOptions = [
  { label: '通用', value: 'general' },
  { label: '全部资料', value: 'all' },
  { label: '文件夹', value: 'folder' },
  { label: '单资料', value: 'material' }
]
const readyMaterials = computed(() => props.materials.filter((item) => item.status === 'ready'))
</script>
```

- [ ] **Step 2: Create MessageBubble component**

Create `frontend/src/components/study/MessageBubble.vue`:

```vue
<template>
  <div :class="['message', role, { error }]">
    <slot>{{ content }}</slot>
  </div>
</template>

<script setup>
defineProps({
  role: { type: String, required: true },
  content: { type: String, default: '' },
  error: { type: Boolean, default: false }
})
</script>
```

- [ ] **Step 3: Create EvidencePanel component**

Create `frontend/src/components/study/EvidencePanel.vue`:

```vue
<template>
  <div class="evidence-list">
    <el-empty v-if="!references.length" description="本次回答没有资料引用" />
    <article v-for="ref in references" :key="referenceKey(ref)" class="source-card">
      <strong>{{ titleFor(ref) }}</strong>
      <p class="muted">{{ metaFor(ref) }}</p>
      <template v-if="isVisual(ref)">
        <p>{{ ref.caption || ref.content_preview || '视觉证据' }}</p>
        <img v-if="urls[ref.asset_id]" :src="urls[ref.asset_id]" :alt="ref.caption || '视觉证据'" class="reference-image" />
        <p v-else class="muted">视觉图片暂不可用</p>
      </template>
      <p v-else>{{ ref.content_preview || ref.content || '暂无片段内容' }}</p>
    </article>
  </div>
</template>

<script setup>
import { onBeforeUnmount, ref, watch } from 'vue'
import { materialApi } from '../../api/modules'

const props = defineProps({ references: { type: Array, default: () => [] } })
const urls = ref({})

function isVisual(ref) {
  return ref.type === 'visual' || ref.type === 'image' || ref.legacy_type === 'image'
}

function titleFor(ref) {
  return ref.material_title || ref.title || `资料 ${ref.material_id || ''}`
}

function metaFor(ref) {
  if (isVisual(ref)) return ref.page_number ? `视觉证据 · 第 ${ref.page_number} 页` : '视觉证据'
  return Number.isInteger(ref.chunk_index) ? `文本片段 ${ref.chunk_index + 1}` : '文本片段'
}

function referenceKey(ref) {
  return isVisual(ref) ? `visual-${ref.asset_id || ref.page_number || ref.caption}` : `text-${ref.material_id}-${ref.chunk_index}-${ref.content_preview}`
}

function revokeAll() {
  Object.values(urls.value).forEach((url) => URL.revokeObjectURL(url))
  urls.value = {}
}

async function loadImages() {
  revokeAll()
  const visualRefs = props.references.filter((ref) => isVisual(ref) && ref.asset_id)
  const entries = await Promise.all(visualRefs.map(async (ref) => {
    try {
      const blob = await materialApi.assetImage(ref.asset_id)
      return [ref.asset_id, URL.createObjectURL(blob)]
    } catch (error) {
      return null
    }
  }))
  urls.value = Object.fromEntries(entries.filter(Boolean))
}

watch(() => props.references, loadImages, { immediate: true, deep: true })
onBeforeUnmount(revokeAll)
</script>
```

- [ ] **Step 4: Update Chat route-query parsing**

In `Chat.vue`, add:

```js
function applyRouteScope() {
  const queryScope = String(route.query.scope_type || '')
  if (['general', 'all', 'folder', 'material'].includes(queryScope)) {
    scopeType.value = queryScope
  }
  if (route.query.prompt) {
    question.value = String(route.query.prompt)
  }
  const routeMaterial = Number(route.query.material_id)
  if (scopeType.value === 'material' && routeMaterial) {
    const material = readyMaterials.value.find((item) => item.id === routeMaterial)
    if (material) selectedMaterial.value = routeMaterial
    else setScopeFallback('链接中的资料不存在或尚未处理完成，已切回全部资料范围')
  }
  const routeFolder = Number(route.query.folder_id)
  if (scopeType.value === 'folder' && routeFolder) {
    const folder = folders.value.find((item) => item.id === routeFolder)
    if (folder) selectedFolder.value = routeFolder
    else setScopeFallback('链接中的文件夹不存在，已切回全部资料范围')
  }
}

function setScopeFallback(message) {
  scopeBanner.value = message
  scopeType.value = 'all'
  selectedFolder.value = null
  selectedMaterial.value = null
}
```

Add `const scopeBanner = ref('')` and call `applyRouteScope()` after materials/folders/history load.

- [ ] **Step 5: Send explicit scope_type and handle retry replacement**

In `ask()`, include:

```js
const payload = { question: text, conversation, scope_type: scopeType.value }
if (scopeType.value === 'folder') payload.folder_id = selectedFolder.value
if (scopeType.value === 'material') payload.material_id = selectedMaterial.value
```

On failure, push an error assistant message with an id:

```js
const errorId = `error-${Date.now()}`
messages.value.push({ id: errorId, role: 'assistant', error: true, content: '这次问答没有成功。可以检查资料范围后重试，或稍后再试。', failedQuestion: text })
lastFailedQuestion.value = text
```

Replace `retryLastFailed()` with:

```js
async function retryLastFailed() {
  if (!lastFailedQuestion.value || asking.value) return
  const failedText = lastFailedQuestion.value
  messages.value = messages.value.filter((message) => !message.error)
  question.value = failedText
  await ask()
}
```

- [ ] **Step 6: Update Chat template to three workbench columns**

Use this structure:

```vue
<div class="chat-layout chat-workbench">
  <aside class="panel chat-sidebar">
    <h3 class="panel-title">历史问答</h3>
    <el-empty v-if="!history.length" description="暂无历史问答" />
    <el-scrollbar v-else height="520px">
      <button v-for="item in history" :key="item.id" type="button" class="history-item" @click="loadHistory(item)">
        <strong>{{ item.question }}</strong>
        <p class="muted">{{ item.answer.slice(0, 58) }}</p>
      </button>
    </el-scrollbar>
  </aside>

  <section class="panel chat-window">
    <div v-if="scopeBanner" class="status-banner warning">{{ scopeBanner }}</div>
    <div class="messages">
      <el-empty v-if="!messages.length && !asking" description="选择范围后开始提问，通用问答不会显示资料引用。" />
      <template v-for="(message, index) in messages" :key="message.id || index">
        <MessageBubble :role="message.role" :content="message.content" :error="message.error" />
        <div v-if="message.role === 'assistant'" class="message-actions">
          <el-button size="small" @click="copyAnswer(message.content)">复制答案</el-button>
          <el-button v-if="message.error && lastFailedQuestion" size="small" type="primary" :loading="asking" @click="retryLastFailed">重试问题</el-button>
        </div>
      </template>
      <div v-if="asking" class="message assistant" role="status" aria-live="polite">AI 正在整理资料并思考…</div>
    </div>
    <div class="chat-input">
      <el-input v-model="question" type="textarea" :rows="2" resize="none" placeholder="请输入学习问题" @keydown.ctrl.enter="ask" />
      <el-button type="primary" :loading="asking" :disabled="!canSend" @click="ask">发送</el-button>
    </div>
  </section>

  <aside class="panel chat-context-panel">
    <h3 class="panel-title">学习范围与证据</h3>
    <ScopeSelector v-model:scope-type="scopeType" v-model:folder-id="selectedFolder" v-model:material-id="selectedMaterial" :folders="folders" :materials="materials" />
    <div v-if="!isScopeReady" class="status-banner warning section-gap">请选择完整范围后再提问。</div>
    <div v-else class="status-banner section-gap">当前范围：{{ currentScopeText }}</div>
    <EvidencePanel :references="activeReferences" />
  </aside>
</div>
```

Add:

```js
const activeReferences = computed(() => [...messages.value].reverse().find((message) => message.references?.length)?.references || [])
```

- [ ] **Step 7: Run frontend build**

Run:

```powershell
Set-Location "D:\学习资料\大数据综合实践\zonghexitong\frontend"
npm run build
```

Expected: PASS.

- [ ] **Step 8: Commit Chat workbench**

Run:

```powershell
git add frontend/src/components/study/ScopeSelector.vue frontend/src/components/study/EvidencePanel.vue frontend/src/components/study/MessageBubble.vue frontend/src/views/Chat.vue frontend/src/styles.css
git commit -m @'
feat: redesign scoped chat workbench

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
'@
```

---

## Task 13: Plans board redesign

**Files:**
- Create: `frontend/src/components/study/PlanCard.vue`
- Create: `frontend/src/components/study/TaskCard.vue`
- Create: `frontend/src/components/study/TaskBoard.vue`
- Modify: `frontend/src/views/Plans.vue`
- Modify: `frontend/src/styles.css`

- [ ] **Step 1: Create PlanCard component**

Create `frontend/src/components/study/PlanCard.vue`:

```vue
<template>
  <article :class="['plan-card', { active }]">
    <div class="plan-card-head">
      <h3>{{ plan.title }}</h3>
      <StatusBadge :code="plan.status || 'unknown'" />
    </div>
    <p class="muted">{{ plan.description || '暂无说明' }}</p>
    <p class="muted">{{ plan.start_date || '未设' }} - {{ plan.end_date || '未设' }}</p>
    <el-progress :percentage="plan.progress_percent || 0" />
    <p class="muted">{{ plan.done_count || 0 }} / {{ plan.task_count || 0 }} 个任务已完成</p>
    <p v-if="plan.next_due_task" class="muted">下一项：{{ plan.next_due_task.title }}</p>
    <div class="plan-card-actions">
      <el-button size="small" @click="$emit('select', plan)">查看任务</el-button>
      <el-button size="small" type="primary" @click="$emit('add-task', plan)">添加任务</el-button>
      <el-button size="small" type="danger" @click="$emit('remove', plan)">删除</el-button>
    </div>
  </article>
</template>

<script setup>
import StatusBadge from './StatusBadge.vue'
defineProps({ plan: { type: Object, required: true }, active: { type: Boolean, default: false } })
defineEmits(['select', 'add-task', 'remove'])
</script>
```

- [ ] **Step 2: Create TaskCard component**

Create `frontend/src/components/study/TaskCard.vue`:

```vue
<template>
  <article class="task-board-card">
    <div class="task-card-title">
      <strong>{{ task.title }}</strong>
      <StatusBadge :code="task.status === 'done' ? 'done' : task.is_overdue ? 'overdue' : 'todo'" />
    </div>
    <p class="muted">{{ task.plan_title || '未归属计划' }}</p>
    <p class="muted">{{ dueLabel }}</p>
    <p v-if="task.description" class="muted">{{ task.description }}</p>
    <div class="task-card-actions">
      <el-button v-if="task.status === 'done'" size="small" @click="$emit('undo', task)">撤销完成</el-button>
      <el-button v-else size="small" type="success" @click="$emit('complete', task)">完成</el-button>
      <el-button size="small" type="danger" @click="$emit('remove', task)">删除</el-button>
    </div>
  </article>
</template>

<script setup>
import { computed } from 'vue'
import StatusBadge from './StatusBadge.vue'
const props = defineProps({ task: { type: Object, required: true } })
defineEmits(['complete', 'undo', 'remove'])
const dueLabel = computed(() => {
  if (!props.task.due_date) return '未安排日期'
  if (props.task.days_until_due === 0) return '今天截止'
  if (props.task.days_until_due === 1) return '明天截止'
  if (props.task.days_until_due < 0) return `已逾期 ${Math.abs(props.task.days_until_due)} 天`
  return props.task.due_date
})
</script>
```

- [ ] **Step 3: Create TaskBoard component**

Create `frontend/src/components/study/TaskBoard.vue`:

```vue
<template>
  <div class="task-board">
    <section v-for="column in columns" :key="column.key" class="task-column">
      <h3>{{ column.title }} <span class="muted">{{ column.items.length }}</span></h3>
      <el-empty v-if="!column.items.length" :description="column.empty" />
      <TaskCard v-for="task in column.items" :key="task.id" :task="task" @complete="$emit('complete', $event)" @undo="$emit('undo', $event)" @remove="$emit('remove', $event)" />
    </section>
  </div>
</template>

<script setup>
import TaskCard from './TaskCard.vue'
defineProps({ columns: { type: Array, default: () => [] } })
defineEmits(['complete', 'undo', 'remove'])
</script>
```

- [ ] **Step 4: Refactor Plans data loading**

In `Plans.vue`, add:

```js
const route = useRoute()
const router = useRouter()
const allTasks = ref([])
const selectedPlanId = ref(Number(route.params.id || route.query.plan_id) || null)
const taskScope = ref(String(route.query.task_scope || 'all'))

async function load() {
  loading.value = true
  try {
    const [planRows, taskRows, todayRows] = await Promise.all([
      planApi.list(),
      taskApi.list(),
      taskApi.today()
    ])
    plans.value = planRows
    allTasks.value = taskRows
    today.value = todayRows
    if (selectedPlanId.value && !plans.value.some((plan) => plan.id === selectedPlanId.value)) {
      ElMessage.warning('链接中的学习计划不存在，已显示全部计划')
      selectedPlanId.value = null
      router.replace('/plans')
    }
  } finally {
    loading.value = false
  }
}
```

- [ ] **Step 5: Add board columns computed**

Add:

```js
const visibleTasks = computed(() => {
  let rows = [...allTasks.value]
  if (selectedPlanId.value) rows = rows.filter((task) => task.plan_id === selectedPlanId.value)
  if (taskScope.value === 'overdue') rows = rows.filter((task) => task.is_overdue)
  return rows
})

const boardColumns = computed(() => {
  const todayTasks = visibleTasks.value.filter((task) => task.status !== 'done' && task.days_until_due === 0)
  const overdueTasks = visibleTasks.value.filter((task) => task.status !== 'done' && task.is_overdue)
  const upcoming = visibleTasks.value.filter((task) => task.status !== 'done' && task.days_until_due > 0)
  const unscheduled = visibleTasks.value.filter((task) => task.status !== 'done' && !task.due_date)
  const completed = visibleTasks.value.filter((task) => task.status === 'done')
  return [
    { key: 'today', title: '今日', empty: '今天没有截止任务', items: [...overdueTasks, ...todayTasks] },
    { key: 'upcoming', title: '即将到期', empty: '暂无未来任务', items: upcoming },
    { key: 'unscheduled', title: '未安排', empty: '暂无未安排任务', items: unscheduled },
    { key: 'completed', title: '已完成', empty: '暂无已完成任务', items: completed }
  ]
})
```

- [ ] **Step 6: Replace plan/table layout with cards and board**

Render:

```vue
<div class="grid two-col">
  <WorkbenchPanel title="学习计划" subtitle="点击计划卡片可聚焦右侧任务。">
    <div class="plan-card-grid">
      <PlanCard
        v-for="plan in plans"
        :key="plan.id"
        :plan="plan"
        :active="plan.id === selectedPlanId"
        @select="selectedPlanId = $event.id"
        @add-task="openTaskDialog($event.id)"
        @remove="removePlan($event.id)"
      />
    </div>
  </WorkbenchPanel>

  <WorkbenchPanel title="任务看板" subtitle="今日、即将到期、未安排和已完成任务。">
    <TaskBoard :columns="boardColumns" @complete="completeTask" @undo="undoTask" @remove="removeTask($event.id)" />
  </WorkbenchPanel>
</div>
```

Add methods:

```js
async function completeTask(task) {
  await taskApi.complete(task.id)
  await load()
}

async function undoTask(task) {
  await taskApi.undo(task.id)
  await load()
}
```

- [ ] **Step 7: Run frontend build**

Run:

```powershell
Set-Location "D:\学习资料\大数据综合实践\zonghexitong\frontend"
npm run build
```

Expected: PASS.

- [ ] **Step 8: Commit Plans board redesign**

Run:

```powershell
git add frontend/src/components/study/PlanCard.vue frontend/src/components/study/TaskCard.vue frontend/src/components/study/TaskBoard.vue frontend/src/views/Plans.vue frontend/src/styles.css
git commit -m @'
feat: redesign study plans board

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
'@
```

---

## Task 14: Responsive and accessibility pass

**Files:**
- Modify: `frontend/src/styles.css`
- Modify touched components only where needed.

- [ ] **Step 1: Add responsive workbench styles**

Append to `frontend/src/styles.css`:

```css
.chat-workbench {
  grid-template-columns: minmax(220px, 280px) minmax(0, 1fr) minmax(240px, 320px);
}

.chat-context-panel,
.chat-sidebar {
  min-width: 0;
}

.task-board {
  display: grid;
  grid-template-columns: repeat(4, minmax(180px, 1fr));
  gap: 14px;
}

.task-column {
  display: grid;
  gap: 10px;
  align-content: start;
  padding: 12px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.54);
}

.task-board-card,
.plan-card,
.visual-asset-card {
  padding: 14px;
  border: 1px solid rgba(47, 128, 237, 0.12);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.76);
}

.visual-asset-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 14px;
}

.visual-preview {
  display: grid;
  place-items: center;
  min-height: 130px;
  border-radius: 14px;
  background: rgba(47, 128, 237, 0.08);
  overflow: hidden;
}

.visual-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

@media (max-width: 1199px) {
  .chat-workbench {
    grid-template-columns: minmax(220px, 280px) minmax(0, 1fr);
  }

  .chat-context-panel {
    grid-column: 1 / -1;
  }

  .task-board {
    grid-template-columns: repeat(2, minmax(180px, 1fr));
  }
}

@media (max-width: 768px) {
  .chat-workbench,
  .task-board,
  .plan-card-grid {
    grid-template-columns: 1fr;
  }

  .chat-input {
    position: sticky;
    bottom: 0;
    background: var(--color-surface);
    padding-top: 12px;
  }
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    scroll-behavior: auto !important;
  }
}
```

- [ ] **Step 2: Verify custom clickable surfaces are buttons or links**

Inspect these files and ensure card actions use `button`, `el-button`, `router-link`, or Element Plus controls rather than clickable `div`:

```text
frontend/src/components/study/MaterialCard.vue
frontend/src/components/study/PlanCard.vue
frontend/src/components/study/TaskCard.vue
frontend/src/views/Dashboard.vue
frontend/src/views/Chat.vue
```

Expected: all custom actions are keyboard-reachable.

- [ ] **Step 3: Run frontend build**

Run:

```powershell
Set-Location "D:\学习资料\大数据综合实践\zonghexitong\frontend"
npm run build
```

Expected: PASS.

- [ ] **Step 4: Manually smoke auth pages after CSS changes**

Run app in dev or preview and verify:

```text
/login loads, form is readable, focus ring visible.
/register loads, form is readable, focus ring visible.
```

Expected: no global CSS regression on auth pages.

- [ ] **Step 5: Commit responsive/accessibility pass**

Run:

```powershell
git add frontend/src/styles.css frontend/src/components/study frontend/src/views
git commit -m @'
style: polish responsive study workbench

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
'@
```

---

## Task 15: Final verification and cleanup

**Files:**
- No planned file changes unless verification finds blockers.

- [ ] **Step 1: Run full backend tests and compileall**

Run:

```powershell
Set-Location "D:\学习资料\大数据综合实践\zonghexitong\backend"
python -m pytest tests -q
python -m compileall "D:\学习资料\大数据综合实践\zonghexitong\backend"
```

Expected: PASS and no syntax failures.

- [ ] **Step 2: Run frontend build**

Run:

```powershell
Set-Location "D:\学习资料\大数据综合实践\zonghexitong\frontend"
npm run build
```

Expected: Vite build completes.

- [ ] **Step 3: Run manual end-to-end verification**

Verify this full flow in browser:

```text
1. Register or log in.
2. Open /dashboard and confirm 今日焦点, core metrics, next actions, and chart text summary.
3. Open /materials?upload=1 and confirm upload dialog opens.
4. Upload a small supported text file and wait for synchronous processing response.
5. Confirm the material appears in card mode and table mode.
6. Open /materials/:id and confirm summary, health metrics, visual assets or empty visual state, and chunks.
7. Click a recommended prompt and confirm /chat pre-fills but does not auto-send.
8. Ask scope_type=general and confirm no evidence is displayed.
9. Ask scope_type=material and confirm references/evidence display when returned.
10. Create a plan and task.
11. Complete and undo the task in /plans.
12. Return to /dashboard and confirm task stats refresh.
13. Edit Profile study goal and confirm AppLayout/Dashboard reflect it.
```

Expected: every step completes without console errors or broken navigation.

- [ ] **Step 4: Check git status**

Run:

```powershell
Set-Location "D:\学习资料\大数据综合实践\zonghexitong"
git status --short
```

Expected: only intended files are modified or all intended implementation commits are already recorded.

- [ ] **Step 5: Commit final fixes only if needed**

If verification required fixes, commit them:

```powershell
git add backend frontend
git commit -m @'
fix: complete redesign verification fixes

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
'@
```

If no fixes were needed, do not commit.

---

## Self-review

### Spec coverage

- Dashboard 今日驾驶舱: Task 9 implements PageHeader, Today Focus, next actions, metrics, knowledge health, AI continuity, and chart summary.
- Materials 知识库: Tasks 2-3 add backend fields/filters; Task 10 implements card/table mode, filters, folder shelf, upload behavior, and AI ask routing.
- Material Detail: Task 11 implements knowledge object detail, health metrics, visual assets, chunks, and prompt-prefill links.
- Chat AI 学习会话: Task 5 adds explicit backend scope and normalized references; Task 12 implements three-column frontend workbench, query parsing, pending/retry, and evidence panel.
- Plans 学习计划: Task 4 adds task filters/computed fields; Task 13 implements plan cards, task board, `/plans/:id`, completion/undo, and selected scope.
- Profile: Task 8 implements study goal/topbar continuity and local preferences.
- State/error/fallback requirements: Tasks 2-5 cover backend validation and fields; Tasks 7-15 cover frontend safe defaults, empty guides, disabled actions, responsive and accessibility checks.
- Testing requirements: Tasks 1-6 cover backend TDD; Task 15 covers build/manual end-to-end verification.

### Placeholder scan

The plan intentionally uses the domain status string `todo`; that is not a placeholder. The plan does not contain unresolved implementation placeholders such as "TBD", "fill in details", or "write tests for the above" without code. Every backend task has specific test code and commands. Every frontend task names exact files, components, code snippets, and build commands.

### Type and naming consistency

- Material metadata uses `visual_asset_count`, `ready_visual_asset_count`, `failed_visual_asset_count`, and `preview_asset_id` consistently.
- Dashboard enhanced fields use `today_focus`, `knowledge_health`, `active_plan_summary`, `next_actions`, and `ai_continuity`.
- Chat scope uses `scope_type=general|all|folder|material`.
- Task board uses `today`, `upcoming`, `unscheduled`, and `completed` scopes/columns.
- Study preferences use `studyhub.defaultScope`, `studyhub.answerStyle`, `studyhub.evidenceExpanded`, and `studyhub.defaultTaskMinutes`.

---

## Execution handoff

Plan complete and saved to `docs/superpowers/plans/2026-06-08-personal-learning-system-redesign.md`.

Two execution options:

1. **Subagent-Driven (recommended)** - Dispatch a fresh subagent per task, review between tasks, fast iteration.
2. **Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints.
