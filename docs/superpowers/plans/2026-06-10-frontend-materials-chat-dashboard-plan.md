# Frontend Materials Chat Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Connect the Phase A backend contracts to the Vue learning workbench: material move/reindex UI, safe assistant Markdown, persistent chat workbench with evidence panel, and dashboard Pomodoro/focus charts.

**Architecture:** Keep the existing Vue 3 + Element Plus + axios layout. Add small focused utilities/components (`renderMarkdown`, `MoveMaterialDialog`, `PomodoroTimer`, `StudyDurationChart`) and wire existing pages to backend contracts. Backend APIs are authoritative; the frontend merges returned material/message/session objects instead of inventing local state.

**Tech Stack:** Vue 3 Composition API, Element Plus, axios, ECharts, Vite, Vitest, markdown-it, DOMPurify.

---

## Dependencies

Start only after these backend plans pass their focused tests:

1. `2026-06-10-backend-contracts-materials-plan.md`
2. `2026-06-10-backend-chat-focus-plan.md`

## File structure and responsibilities

- Modify: `frontend/package.json`, `frontend/package-lock.json` — add `markdown-it`, `dompurify`, `vitest`, `jsdom`, `test:unit` if missing.
- Modify: `frontend/src/api/http.js` — expose normalized backend envelope fields on rejected errors.
- Modify: `frontend/src/api/modules.js` — material/chat/focus/stats API methods.
- Create: `frontend/src/utils/renderMarkdown.js` — trusted renderer boundary.
- Create: `frontend/src/utils/renderMarkdown.test.js` — XSS/formatting unit tests.
- Create: `frontend/src/components/study/MoveMaterialDialog.vue` — reusable material move dialog.
- Create: `frontend/src/components/study/PomodoroTimer.vue` — local timer that persists only completed sessions.
- Create: `frontend/src/components/study/StudyDurationChart.vue` — focus duration bar chart with text summary.
- Modify: `frontend/src/components/study/MaterialCard.vue` — move/reindex/index-state actions.
- Modify: `frontend/src/components/study/StatusBadge.vue` — Phase A statuses.
- Modify: `frontend/src/components/study/MessageBubble.vue` — sanitized assistant Markdown.
- Modify: `frontend/src/components/study/ScopeSelector.vue` — `uncategorized` scope and a11y names.
- Modify: `frontend/src/components/study/EvidencePanel.vue` — citations/full material/scope tabs and image fallback.
- Modify: `frontend/src/views/Materials.vue` — move dialog, table dropdown, reindex polling cleanup.
- Modify: `frontend/src/views/MaterialDetail.vue` — move/reindex status and image fallback.
- Modify: `frontend/src/views/Chat.vue` — persistent conversation workbench.
- Modify: `frontend/src/views/Dashboard.vue` — Pomodoro, focus seconds, focus duration chart, plan/checklist priority.
- Modify: `frontend/src/components/AppLayout.vue` — navigation order if not already done.
- Modify: `frontend/src/styles.css` — layout, Markdown, material/chat/dashboard styles needed by this functional plan.

---

### Task 1: API modules and error metadata

**Files:**
- Modify: `frontend/src/api/http.js`
- Modify: `frontend/src/api/modules.js`

- [ ] **Step 1: Normalize API errors**

Ensure rejected axios errors expose:

- `error.apiError`
- `error.apiCode`
- `error.apiMessage`
- `error.retryable`
- `error.status`

These values must come from backend `{ message, error: { code, message, details, field_errors, retryable, request_id } }` envelopes while preserving current Element Plus toast behavior.

- [ ] **Step 2: Add API methods**

Ensure `modules.js` exposes:

```js
materialApi.moveFolder(id, data)
materialApi.reindex(id, data = {})
materialApi.indexStatus(id)
chatApi.conversations(params)
chatApi.createConversation(data)
chatApi.deleteConversation(id)
chatApi.messages(id, params)
chatApi.sendMessage(id, data)
chatApi.retryMessage(id, data)
focusApi.createSession(data)
statsApi.focusDurationTrend(params)
```

Keep existing legacy API methods used by current pages.

- [ ] **Step 3: Build**

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong\frontend"
npm run build
Pop-Location
```

Expected: PASS.

- [ ] **Step 4: Commit**

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong"
git add frontend/src/api/http.js frontend/src/api/modules.js
git commit -m @'
feat: add phase a frontend api contracts

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
'@
Pop-Location
```

---

### Task 2: Safe Markdown renderer with unit tests

**Files:**
- Modify: `frontend/package.json`
- Modify: `frontend/package-lock.json`
- Create: `frontend/src/utils/renderMarkdown.js`
- Create: `frontend/src/utils/renderMarkdown.test.js`
- Modify: `frontend/src/components/study/MessageBubble.vue`

- [ ] **Step 1: Install dependencies and test script**

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong\frontend"
npm install markdown-it dompurify
npm install -D vitest jsdom
Pop-Location
```

Add script:

```json
"test:unit": "vitest run --environment jsdom"
```

- [ ] **Step 2: Create renderer**

`renderMarkdown(source)` must:

- Use `markdown-it` with raw HTML disabled.
- Use DOMPurify sanitization.
- Allow headings, paragraphs, lists, blockquotes, links, inline code, code blocks, and tables.
- Strip script/style/iframe/object/embed/form/input tags.
- Strip event handlers and inline style attributes.
- Block `javascript:`, `data:`, and `vbscript:` links.
- Add `target="_blank" rel="noopener noreferrer"` to links.

- [ ] **Step 3: Add tests**

Tests must cover:

- bold/list/code rendering.
- `<script>` removed.
- `<img onerror>` handler removed.
- `javascript:` link blocked.
- `<iframe>` removed.
- style injection removed.
- safe external link gets target/rel.

- [ ] **Step 4: Use renderer in MessageBubble**

Assistant messages render sanitized HTML; user messages render plain text. Citations remain structured UI outside Markdown.

- [ ] **Step 5: Run tests and build**

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong\frontend"
npm run test:unit
npm run build
Pop-Location
```

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong"
git add frontend/package.json frontend/package-lock.json frontend/src/utils/renderMarkdown.js frontend/src/utils/renderMarkdown.test.js frontend/src/components/study/MessageBubble.vue
git commit -m @'
feat: render assistant markdown safely

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
'@
Pop-Location
```

---

### Task 3: Materials move and reindex UI

**Files:**
- Create: `frontend/src/components/study/MoveMaterialDialog.vue`
- Modify: `frontend/src/components/study/MaterialCard.vue`
- Modify: `frontend/src/components/study/StatusBadge.vue`
- Modify: `frontend/src/views/Materials.vue`
- Modify: `frontend/src/views/MaterialDetail.vue`
- Modify: `frontend/src/styles.css`

- [ ] **Step 1: Add reusable move dialog**

Create a dialog with `v-model`, `v-model:folder-id`, `material`, `folders`, `loading`, and `submit(targetFolderId)` event. It must include an explicit `未分类` option with `:value="null"`.

- [ ] **Step 2: Add status labels**

`StatusBadge` should support `not_indexed`, `queued`, `running`, `ready`, `stale`, `sync_failed`, `failed_timeout`, `failed_error`, and `generating`.

- [ ] **Step 3: Update material cards**

Cards must show index state, allow ask AI when `status === 'ready' || active_index_generation`, and expose `move`, `reindex`, and `remove` from a visible/keyboard-accessible action menu.

- [ ] **Step 4: Update Materials view**

Add:

- move dialog state and `moveMaterial(targetFolderId)`.
- `mergeMaterial(material)` helper.
- row loading state.
- table operation column as `查看 + 问答 + 更多` or `查看 + 更多` depending available width.
- reindex polling: every 2s for 60s, then every 5s until 5min, stop on `succeeded/failed/cancelled/stale`, cleanup timers in `onBeforeUnmount()`.

- [ ] **Step 5: Update MaterialDetail**

Add move/reindex actions, index status display, and the same polling cleanup pattern. Missing image blob loads should show accessible fallback copy rather than blank content.

- [ ] **Step 6: Build**

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong\frontend"
npm run build
Pop-Location
```

Expected: PASS.

- [ ] **Step 7: Commit**

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong"
git add frontend/src/components/study/MoveMaterialDialog.vue frontend/src/components/study/MaterialCard.vue frontend/src/components/study/StatusBadge.vue frontend/src/views/Materials.vue frontend/src/views/MaterialDetail.vue frontend/src/styles.css
git commit -m @'
feat: add material move and reindex frontend flow

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
'@
Pop-Location
```

---

### Task 4: Persistent chat workbench and evidence panel

**Files:**
- Modify: `frontend/src/views/Chat.vue`
- Modify: `frontend/src/components/study/EvidencePanel.vue`
- Modify: `frontend/src/components/study/ScopeSelector.vue`
- Modify: `frontend/src/components/study/MessageBubble.vue`
- Modify: `frontend/src/styles.css`

- [ ] **Step 1: Extend scope selector**

Add `uncategorized`; emit `{ scope_type: 'uncategorized', folder_id: null }`; keep folder/material dependent selects only when needed.

- [ ] **Step 2: Rework Chat state**

Use canonical backend conversations/messages. Keep legacy `chatApi.history()` only as fallback when canonical endpoints are unavailable. Store latest citation for right panel.

- [ ] **Step 3: Implement conversation actions**

Support load/create/select/delete. Delete must use confirmation and switch to the next active conversation or empty state.

- [ ] **Step 4: Implement send/retry**

Use:

- `chatApi.sendMessage(activeConversation.id, { content, scope, request_id })`
- `chatApi.retryMessage(message.id, { request_id })`

Failed assistant messages should show status, `error_code`, and retry button when `retryable`.

- [ ] **Step 5: Expand EvidencePanel**

Tabs/sections:

- `引用片段`: structured citation cards.
- `完整资料`: load detail for selected citation and show summary/chunks/assets.
- `学习范围`: compact chips and expandable selector.

Image blob failures show accessible placeholders with caption/material/recovery copy and no infinite retry.

- [ ] **Step 6: Add internal scroll styles**

Chat desktop uses left/middle/right internal scroll. Page body is not the transcript scroll container. Long Markdown/code/table content does not cause body horizontal scroll.

- [ ] **Step 7: Run tests and build**

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong\frontend"
npm run test:unit
npm run build
Pop-Location
```

Expected: PASS.

- [ ] **Step 8: Commit**

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong"
git add frontend/src/views/Chat.vue frontend/src/components/study/EvidencePanel.vue frontend/src/components/study/ScopeSelector.vue frontend/src/components/study/MessageBubble.vue frontend/src/styles.css
git commit -m @'
feat: add persistent chat workbench and evidence panel

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
'@
Pop-Location
```

---

### Task 5: Dashboard Pomodoro, focus chart, navigation order

**Files:**
- Create: `frontend/src/components/study/PomodoroTimer.vue`
- Create: `frontend/src/components/study/StudyDurationChart.vue`
- Modify: `frontend/src/components/AppLayout.vue`
- Modify: `frontend/src/views/Dashboard.vue`
- Modify: `frontend/src/styles.css`

- [ ] **Step 1: Navigation order**

Ensure navigation order is:

1. 今日驾驶舱
2. 学习计划
3. 知识库
4. AI 学习会话
5. 个人设置

Use SVG icon components, not Chinese glyphs.

- [ ] **Step 2: Add PomodoroTimer**

Timer state is local-only for running/paused/reset. Persist only completed sessions with `focusApi.createSession()`. Payload must include `client_session_id`, `started_at`, `ended_at`, `duration_seconds`, `planned_seconds`, `study_date`, `timezone_offset_minutes`, `source: 'pomodoro'`. Use `aria-live="polite"` for timer status.

- [ ] **Step 3: Add StudyDurationChart**

Render ECharts bar chart from `[{ date, duration_seconds }]`, include text summary, resize on window resize, dispose on unmount.

- [ ] **Step 4: Update Dashboard**

Show:

- Today focus seconds.
- Active plan/today checklist above material stats.
- Pomodoro timer in the top dashboard region.
- Focus duration chart near task trend.
- Material/AI sections lower on the page.

On Pomodoro completion, refresh dashboard and trend data.

- [ ] **Step 5: Run tests and build**

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong\frontend"
npm run test:unit
npm run build
Pop-Location
```

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong"
git add frontend/src/components/study/PomodoroTimer.vue frontend/src/components/study/StudyDurationChart.vue frontend/src/components/AppLayout.vue frontend/src/views/Dashboard.vue frontend/src/styles.css
git commit -m @'
feat: add dashboard focus duration and pomodoro flow

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
'@
Pop-Location
```

---

### Task 6: Full frontend verification

- [ ] **Step 1: Unit tests**

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong\frontend"
npm run test:unit
Pop-Location
```

Expected: PASS.

- [ ] **Step 2: Production build**

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong\frontend"
npm run build
Pop-Location
```

Expected: PASS.

- [ ] **Step 3: Manual checks**

Verify:

- Materials can move to folder and back to uncategorized using `folder_id: null`.
- Reindex shows queued/running/terminal states and polling stops.
- Assistant Markdown renders safe formatting and XSS payloads do not execute.
- Chat supports create/switch/delete/send/retry/citations/evidence panel.
- Dashboard Pomodoro completion posts once and refreshes focus seconds/chart.
- Widths `390px`, `768px`, `1024px`, `1440px` have no body-level horizontal scroll.

## Final verification commands

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong\backend"
python -m pytest tests -v
Pop-Location
Push-Location "D:\学习资料\大数据综合实践\zonghexitong\frontend"
npm run test:unit
npm run build
Pop-Location
```

Expected: all commands PASS.
