# Backend Chat and Focus Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add durable chat conversations/messages/citations, legacy ChatHistory migration/fallback, stable AI timeout/retry/delete behavior, completed FocusSession persistence, and dashboard focus-duration trends.

**Architecture:** Keep the existing Flask + SQLAlchemy + JWT route style and add narrow persistent tables beside the existing `ChatHistory` table. New chat endpoints become canonical; legacy `/api/chat` and `/api/chat/history` remain readable through migration-first, adapter-fallback compatibility. Focus sessions are write-on-completion only, and stats aggregate from persisted `FocusSession` rows with zero-filled daily trends.

**Tech Stack:** Flask, Flask-JWT-Extended, Flask-SQLAlchemy, SQLite/MySQL-compatible schema, pytest, existing RAG/AI services.

---

## File structure and responsibilities

- Create: `backend/models/focus.py` — `FocusSession` model and serialization.
- Create: `backend/routes/focus.py` — `POST /api/focus-sessions`.
- Create: `backend/services/chat_history_adapter.py` — legacy `ChatHistory` migration and fallback helpers.
- Create: `backend/tests/test_chat_conversations_api.py` — conversation/message/citation/migration/delete/timeout/retry/idempotency tests.
- Create: `backend/tests/test_focus_stats_api.py` — focus validation/idempotency/dashboard/trend tests.
- Modify: `backend/models/chat.py` — keep `ChatHistory`; add `Conversation`, `Message`, `Citation`.
- Modify: `backend/models/__init__.py` — export chat/focus models.
- Modify: `backend/app.py` — register `focus_bp`.
- Modify: `backend/services/ai_service.py` — stable timeout/upstream exception types.
- Modify: `backend/routes/chat.py` — canonical conversation/message endpoints plus legacy compatibility.
- Modify: `backend/services/stats_service.py` — active conversation and focus aggregations.
- Modify: `backend/routes/stats.py` — `GET /api/stats/focus-duration-trend?days=7`.
- Modify: `backend/tests/conftest.py` — chat/focus fixtures.
- Modify: `backend/tests/test_chat_stats_api.py` — dashboard compatibility expectations.

---

### Task 1: Persistent chat and focus models

**Files:**
- Modify: `backend/models/chat.py`
- Create: `backend/models/focus.py`
- Modify: `backend/models/__init__.py`
- Modify: `backend/tests/conftest.py`
- Create: `backend/tests/test_chat_conversations_api.py`
- Create: `backend/tests/test_focus_stats_api.py`

- [ ] **Step 1: Add failing serialization tests**

Create tests that assert:

- `Conversation.to_dict()` includes `id`, `title`, `default_scope`, `status`, timestamps, and `legacy_history_id`.
- `Message.to_dict(include_citations=True)` includes `id`, `conversation_id`, `role`, `content`, `status`, `scope_snapshot`, `request_id`, `parent_message_id`, `retry_of_message_id`, `error_code`, `retryable`, timestamps, `citations`, and `references` alias for assistant messages.
- `Citation.to_dict()` includes type/material/folder/chunk/asset/page/caption/preview/score/source/generation fields.
- `FocusSession.to_dict()` includes `id`, `client_session_id`, `status`, `duration_seconds`, `planned_seconds`, `study_date`, `source`, timestamps.

- [ ] **Step 2: Run model tests and verify failure**

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong\backend"
python -m pytest tests\test_chat_conversations_api.py tests\test_focus_stats_api.py -q
Pop-Location
```

Expected before implementation: FAIL because new models/fixtures do not exist.

- [ ] **Step 3: Implement models**

Add models:

- `Conversation`: `id`, `user_id`, `title`, `default_scope_json`, `status`, `legacy_history_id`, `created_at`, `updated_at`, `deleted_at`.
- `Message`: `id`, `conversation_id`, `user_id`, `role`, `content`, `status`, `scope_snapshot_json`, `request_id`, `parent_message_id`, `retry_of_message_id`, `error_code`, `retryable`, `created_at`, `updated_at`.
- `Citation`: `id`, `message_id`, `type`, `material_id`, `material_title_snapshot`, `folder_id_snapshot`, `folder_name_snapshot`, `chunk_id`, `chunk_index`, `asset_id`, `page_number`, `asset_index`, `caption`, `preview`, `score`, `source_state`, `generation`, `created_at`.
- `FocusSession`: `id`, `user_id`, `client_session_id`, `started_at`, `ended_at`, `duration_seconds`, `planned_seconds`, `study_date`, `timezone_offset_minutes`, `source`, `status`, `created_at`, unique `(user_id, client_session_id)`.

- [ ] **Step 4: Add fixtures**

In `backend/tests/conftest.py`, add:

- `make_conversation(user, title="新会话", status="active")`
- `make_message(conversation, role="user", content="问题", status="succeeded", request_id=None)`
- `make_citation(message, material=None, preview="引用片段")`
- `make_focus_session(user, study_date=date.today(), duration_seconds=1500, client_session_id="pomo-test")`

- [ ] **Step 5: Verify model tests pass**

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong\backend"
python -m pytest tests\test_chat_conversations_api.py tests\test_focus_stats_api.py -q
Pop-Location
```

Expected: PASS for serialization/fixture tests in this task.

- [ ] **Step 6: Commit**

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong"
git add backend/models/chat.py backend/models/focus.py backend/models/__init__.py backend/tests/conftest.py backend/tests/test_chat_conversations_api.py backend/tests/test_focus_stats_api.py
git commit -m @'
feat: add persistent chat and focus models

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
'@
Pop-Location
```

---

### Task 2: ChatHistory migration and conversation list/create/delete APIs

**Files:**
- Create: `backend/services/chat_history_adapter.py`
- Modify: `backend/routes/chat.py`
- Modify: `backend/tests/test_chat_conversations_api.py`

- [ ] **Step 1: Add failing API tests**

Test these cases:

- `GET /api/chat/conversations` migrates one `ChatHistory` row into one active `Conversation` with one user and one assistant message.
- Re-running list is idempotent and does not duplicate migrated conversations.
- `POST /api/chat/conversations` creates an active empty conversation with default scope.
- `DELETE /api/chat/conversations/<id>` soft deletes, cancels generating messages, and excludes from list.
- Cross-user conversation access/delete returns `404`.

- [ ] **Step 2: Implement adapter**

Create `migrate_chat_history_for_user(user_id)`:

- For each unmigrated `ChatHistory`, create one `Conversation` with `legacy_history_id`.
- Create a user `Message` from `question` and an assistant `Message` from `answer`.
- Convert legacy `references_json` into `Citation` rows where possible.
- Use `created_at` from legacy rows for migrated rows.
- On exception, rollback, log, and return `{ "migrated": 0, "failed": true }` without breaking legacy reads.

- [ ] **Step 3: Implement routes**

Add:

- `GET /api/chat/conversations?page=1&limit=30`
- `POST /api/chat/conversations`
- `DELETE /api/chat/conversations/<int:conversation_id>`

Use stable error envelopes for validation and not-found responses.

- [ ] **Step 4: Verify tests**

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong\backend"
python -m pytest tests\test_chat_conversations_api.py -q
Pop-Location
```

Expected: PASS for migration/list/create/delete tests.

- [ ] **Step 5: Commit**

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong"
git add backend/services/chat_history_adapter.py backend/routes/chat.py backend/tests/test_chat_conversations_api.py
git commit -m @'
feat: add conversation APIs and legacy chat migration

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
'@
Pop-Location
```

---

### Task 3: Message send, citations, timeout, retry, legacy compatibility

**Files:**
- Modify: `backend/services/ai_service.py`
- Modify: `backend/routes/chat.py`
- Modify: `backend/services/chat_history_adapter.py`
- Modify: `backend/tests/test_chat_conversations_api.py`
- Modify: `backend/tests/test_chat_stats_api.py`

- [ ] **Step 1: Add failing tests**

Cover:

- `POST /api/chat/conversations/<id>/messages` persists user and assistant messages.
- RAG references become `Citation` rows and response `citations`.
- Duplicate `request_id` returns existing message pair.
- AI timeout returns `504`, `error.code == "AI_TIMEOUT"`, assistant `failed_timeout`, `retryable: true`.
- Upstream AI error returns `502`, `error.code == "UPSTREAM_AI_ERROR"`, assistant `failed_error`, `retryable: true`.
- `POST /api/chat/messages/<id>/retry` creates a new assistant attempt with `retry_of_message_id`.
- Retry rejects user/succeeded/deleted/cross-user messages.
- Legacy `POST /api/chat` still returns old `answer` / `references` shape on success.

- [ ] **Step 2: Add AI exception types**

In `ai_service.py`, add `AIServiceTimeoutError` and `UpstreamAIError`; wrap outbound request timeouts and non-timeout request failures into those types. Keep disabled-AI fallback behavior unchanged.

- [ ] **Step 3: Implement message routes**

Add:

- `GET /api/chat/conversations/<int:conversation_id>/messages?page=1&limit=50`
- `POST /api/chat/conversations/<int:conversation_id>/messages`
- `POST /api/chat/messages/<int:message_id>/retry`

Message send flow:

1. Validate active conversation ownership.
2. Deduplicate by `request_id`.
3. Save user message as `succeeded`.
4. Save assistant placeholder as `generating`.
5. Use `AIService.answer` for `general`, otherwise `RAGService.answer`.
6. Success: assistant `succeeded`, save Markdown and citations.
7. Timeout: assistant `failed_timeout`, return `504` envelope.
8. Upstream failure: assistant `failed_error`, return `502` envelope.
9. Re-check deleted conversation before final success so late replies cannot resurrect deleted conversations.

- [ ] **Step 4: Update legacy endpoint**

Keep `POST /api/chat` response compatible while also creating canonical rows. Timeout/upstream failures must return stable envelopes rather than black-box `500`.

- [ ] **Step 5: Verify chat tests**

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong\backend"
python -m pytest tests\test_chat_conversations_api.py tests\test_chat_stats_api.py -q
Pop-Location
```

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong"
git add backend/services/ai_service.py backend/routes/chat.py backend/services/chat_history_adapter.py backend/tests/test_chat_conversations_api.py backend/tests/test_chat_stats_api.py
git commit -m @'
feat: persist chat messages with retryable AI failures

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
'@
Pop-Location
```

---

### Task 4: FocusSession API

**Files:**
- Create: `backend/routes/focus.py`
- Modify: `backend/app.py`
- Modify: `backend/services/stats_service.py`
- Modify: `backend/tests/test_focus_stats_api.py`

- [ ] **Step 1: Add failing focus tests**

Cover:

- Valid completed Pomodoro creates a session and returns `201`.
- Duplicate `client_session_id` returns `200` and does not double-count.
- `duration_seconds < 60` and `duration_seconds > 14400` return `400`.
- Bad `study_date` returns `400`.
- Timestamp/duration mismatch greater than 5 seconds returns `400`.
- Cross-user duplicate `client_session_id` is allowed.

- [ ] **Step 2: Implement route**

Create `focus_bp` with `POST /api/focus-sessions`. Validate payload and return:

```json
{
  "focus_session": {},
  "today_focus_seconds": 1500
}
```

Use `VALIDATION_ERROR` envelopes for validation failures.

- [ ] **Step 3: Register route and stat helper**

Register in `app.py` with prefix `/api/focus-sessions`. Add `today_focus_seconds(user_id, target_date=None)` in `stats_service.py`.

- [ ] **Step 4: Verify focus tests**

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong\backend"
python -m pytest tests\test_focus_stats_api.py -q
Pop-Location
```

Expected: PASS for API tests.

- [ ] **Step 5: Commit**

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong"
git add backend/routes/focus.py backend/app.py backend/services/stats_service.py backend/tests/test_focus_stats_api.py
git commit -m @'
feat: add completed focus session API

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
'@
Pop-Location
```

---

### Task 5: Focus trends and conversation-backed dashboard stats

**Files:**
- Modify: `backend/services/stats_service.py`
- Modify: `backend/routes/stats.py`
- Modify: `backend/tests/test_chat_stats_api.py`
- Modify: `backend/tests/test_focus_stats_api.py`

- [ ] **Step 1: Add failing stats tests**

Cover:

- `GET /api/stats/focus-duration-trend` returns 7 zero-filled days by default.
- `days=1` and `days=30` accepted; `days=0`, `days=31`, non-integer rejected.
- Multiple focus sessions on the same date are summed.
- Dashboard includes `today_focus_seconds`, `today_checklist`, `task_trend`, `focus_duration_trend`, `material_type_summary`, `folder_summary`.
- Dashboard keeps existing `today_focus`, `next_actions`, `knowledge_health`, `active_plan_summary`, `ai_continuity`, `recent_chats`.
- Dashboard recent chats prefer active conversations and exclude deleted; fall back to legacy `ChatHistory` if no conversations exist.

- [ ] **Step 2: Implement trend helper and route**

Add `focus_duration_trend(user_id, days=7)` in `stats_service.py` and `GET /api/stats/focus-duration-trend` in `routes/stats.py`.

- [ ] **Step 3: Update dashboard stats**

Add required Phase A fields while preserving existing tests. Prefer active conversations for chat counts/recent rows, but fallback to `ChatHistory`.

- [ ] **Step 4: Verify stats tests**

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong\backend"
python -m pytest tests\test_chat_stats_api.py tests\test_focus_stats_api.py -q
Pop-Location
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong"
git add backend/services/stats_service.py backend/routes/stats.py backend/tests/test_chat_stats_api.py backend/tests/test_focus_stats_api.py
git commit -m @'
feat: add focus trends to dashboard stats

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
'@
Pop-Location
```

---

### Task 6: Full backend verification

- [ ] **Step 1: Run focused suites**

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong\backend"
python -m pytest tests\test_chat_conversations_api.py -q
python -m pytest tests\test_focus_stats_api.py -q
python -m pytest tests\test_chat_stats_api.py -q
python -m pytest tests\test_tasks_plans_api.py -q
Pop-Location
```

Expected: PASS.

- [ ] **Step 2: Run full backend suite**

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong\backend"
python -m pytest tests -q
Pop-Location
```

Expected: PASS.

## Final acceptance

- [ ] `ChatHistory` remains readable and is not deleted.
- [ ] Canonical conversations/messages/citations support create/list/delete/send/retry.
- [ ] AI timeout and upstream failures save failed assistant placeholders and return stable envelopes.
- [ ] Completed FocusSession submissions are idempotent per user.
- [ ] Dashboard and trend endpoints expose focus duration fields.
- [ ] Existing chat/stats/tasks/material tests pass.
