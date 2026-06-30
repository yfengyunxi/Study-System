# Main Learning Flow Repair Implementation Plan Index

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the approved Phase A repair in small, independently testable slices: backend contracts first, then frontend workbenches, then visual/accessibility hardening.

**Architecture:** This index intentionally splits Phase A into four focused implementation plans because the spec spans independent subsystems with different risk profiles. Backend plans establish stable API/state contracts before frontend plans consume them. The final visual plan hardens shared UI after feature behavior is working.

**Tech Stack:** Flask, SQLAlchemy, Flask-JWT-Extended, pytest, Vue 3 Composition API, Element Plus, axios, ECharts, Vite, Vitest, markdown-it, DOMPurify.

---

## Source spec

`D:\学习资料\大数据综合实践\zonghexitong\docs\superpowers\specs\2026-06-09-main-learning-flow-repair-design.md`

## Plan files

Implement these in order:

1. `D:\学习资料\大数据综合实践\zonghexitong\docs\superpowers\plans\2026-06-10-backend-contracts-materials-plan.md`
   - Normalized API errors.
   - Scope schema including uncategorized.
   - Material move/classify.
   - SQL/RAG metadata sync.
   - Reindex jobs and asset image errors.

2. `D:\学习资料\大数据综合实践\zonghexitong\docs\superpowers\plans\2026-06-10-backend-chat-focus-plan.md`
   - Persistent conversations/messages/citations.
   - ChatHistory migration-first with adapter fallback.
   - AI timeout/retry/delete semantics.
   - FocusSession and dashboard study-duration stats.

3. `D:\学习资料\大数据综合实践\zonghexitong\docs\superpowers\plans\2026-06-10-frontend-materials-chat-dashboard-plan.md`
   - Frontend API modules.
   - Safe Markdown renderer and tests.
   - Materials move/reindex UI.
   - Chat workbench and right evidence panel.
   - Dashboard Pomodoro, study duration charts, and navigation order.

4. `D:\学习资料\大数据综合实践\zonghexitong\docs\superpowers\plans\2026-06-10-visual-responsive-accessibility-plan.md`
   - Shared visual tokens.
   - Button/input/icon hardening.
   - Profile compaction.
   - Responsive and accessibility verification.

## Required execution discipline

- Use TDD for backend contracts and frontend Markdown utilities.
- Commit after each task inside each plan after the listed verification commands pass.
- Do not start a frontend feature before its backend API contract plan has passed.
- Do not start visual/accessibility hardening until the feature plans pass build/tests.

## Full-suite final verification

Run after all plan files are complete:

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong\backend"
python -m pytest tests
Pop-Location
Push-Location "D:\学习资料\大数据综合实践\zonghexitong\frontend"
npm run test:unit
npm run build
Pop-Location
```

Manual browser verification after the commands pass:

```text
1. Move an uncategorized material into a folder, then back to uncategorized.
2. Start a material reindex and observe queued/running/succeeded or failed UI.
3. Open an image citation whose file is missing and verify accessible fallback copy.
4. Create a chat conversation, send a scoped message, delete the conversation, and retry a simulated timeout.
5. Confirm assistant Markdown renders bold/list/code safely and XSS payloads do not execute.
6. Complete a Pomodoro session and verify dashboard today-focus seconds and chart refresh.
7. Check 390px, 768px, 1024px, and 1440px widths for no body-level horizontal scroll.
```
