# Visual Responsive Accessibility Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Harden the Phase A frontend visual system so Dashboard, Materials, Chat, Profile, AppLayout, and shared study components use consistent tokens, accessible controls/icons, compact Profile layout, and verified responsive behavior at 360/390px, 768px, 1024px, and 1366/1440px.

**Architecture:** Keep the existing Vue 3 + Element Plus + global CSS architecture. Centralize visual tokens and control sizing in `styles.css`, then apply those tokens through small Vue SFC changes; do not introduce a full design-system rewrite or backend changes. Use `@element-plus/icons-vue` for structural icons and preserve visible text labels for navigation and actions.

**Tech Stack:** Vue 3 SFC, Vite, Element Plus, `@element-plus/icons-vue`, CSS custom properties, ECharts.

---

## Dependencies

Run after `2026-06-10-frontend-materials-chat-dashboard-plan.md` passes `npm run test:unit` and `npm run build`. This plan should not change backend behavior.

## File map

- Modify: `frontend/src/styles.css` — shared tokens, Element Plus overrides, responsive rules, Profile compaction, Chat bounded layout, focus utilities.
- Modify: `frontend/src/components/AppLayout.vue` — navigation order, SVG nav icons, active state semantics.
- Modify: `frontend/src/components/study/MetricCard.vue` — component icons instead of structural text glyphs.
- Modify: `frontend/src/views/Dashboard.vue` — SVG metric icons and chart summaries.
- Modify: `frontend/src/views/Materials.vue` — compact table actions and overflow containment.
- Modify: `frontend/src/views/Chat.vue` — responsive drawer/sheet controls, internal scroll, composer accessibility.
- Modify: `frontend/src/views/Profile.vue` — compact layout only.
- Modify: `frontend/src/components/study/PageHeader.vue`, `WorkbenchPanel.vue`, `FolderShelf.vue`, `MaterialCard.vue`, `MaterialFilters.vue`, `ScopeSelector.vue`, `MessageBubble.vue`, `EvidencePanel.vue`, `VisualAssetGrid.vue`, `EmptyGuide.vue` — control sizing, labels, image fallback copy, wrapping.
- Modify: `frontend/src/views/Plans.vue` — replace metric glyph icons if still present.

---

### Task 1: Shared visual tokens and control baseline

**Files:**
- Modify: `frontend/src/styles.css`

- [ ] **Step 1: Add token groups**

Add or merge variables for spacing (`--space-1` through `--space-8`), controls (`--control-height`, `--control-height-sm`), icon sizes, focus ring, elevation, z-index, and motion. Keep the existing warm palette; do not replace all colors/fonts.

- [ ] **Step 2: Add global hardening**

Add:

- `html, body, #app { min-height: 100%; overflow-x: clip; }`
- readable wrapping for subtitles/messages/source cards/material summaries.
- `.sr-only`, `.desktop-only`, `.tablet-mobile-only`, `.mobile-only`, `.compact-actions`, `.icon-button`, `.touch-target` utilities.
- visible `:focus-visible` rules.
- Element Plus button/input/select minimum hit areas and disabled/loading states.

- [ ] **Step 3: Build**

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong\frontend"
npm run build
Pop-Location
```

Expected: PASS.

---

### Task 2: Replace structural text glyph icons

**Files:**
- Modify: `frontend/src/components/AppLayout.vue`
- Modify: `frontend/src/components/study/MetricCard.vue`
- Modify: `frontend/src/views/Dashboard.vue`
- Modify: `frontend/src/views/Plans.vue`
- Modify: `frontend/src/components/study/EmptyGuide.vue`

- [ ] **Step 1: Replace navigation glyphs**

Replace `今`, `库`, `问`, `划`, `我` structural nav glyphs with Element Plus icon components. Keep brand mark text only as decorative brand.

- [ ] **Step 2: Update MetricCard**

Allow icon props to be Vue components and render them inside `el-icon` with `aria-hidden="true"`.

- [ ] **Step 3: Replace Dashboard/Plans metric glyphs**

Use imported Element Plus icons for metric cards; no Chinese text glyphs or bare checkmark glyphs as structural icons.

- [ ] **Step 4: Build**

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong\frontend"
npm run build
Pop-Location
```

Expected: PASS.

---

### Task 3: Shared study component control hardening

**Files:**
- Modify: `frontend/src/components/study/PageHeader.vue`
- Modify: `frontend/src/components/study/WorkbenchPanel.vue`
- Modify: `frontend/src/components/study/FolderShelf.vue`
- Modify: `frontend/src/components/study/MaterialCard.vue`
- Modify: `frontend/src/components/study/MaterialFilters.vue`
- Modify: `frontend/src/components/study/ScopeSelector.vue`
- Modify: `frontend/src/components/study/EvidencePanel.vue`
- Modify: `frontend/src/components/study/VisualAssetGrid.vue`
- Modify: `frontend/src/styles.css`

- [ ] **Step 1: Header/panel action layout**

Ensure `PageHeader` and `WorkbenchPanel` action slots wrap cleanly and use shared toolbar classes.

- [ ] **Step 2: Icon-only controls**

`FolderShelf`, material action menus, evidence/image fallback controls, and any icon-only buttons must have visible text or `aria-label`. Replace `⋯` with `MoreFilled` where used as a structural control.

- [ ] **Step 3: Filter/scope labels**

Add accessible names to placeholder-only filter/search/select/segmented controls in `MaterialFilters` and `ScopeSelector`.

- [ ] **Step 4: Image fallback copy**

`EvidencePanel` and `VisualAssetGrid` should show source-aware fallback copy when image blobs fail: caption/material/recovery path; no blank image area and no infinite retry.

- [ ] **Step 5: Build**

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong\frontend"
npm run build
Pop-Location
```

Expected: PASS.

---

### Task 4: Materials table/card responsiveness

**Files:**
- Modify: `frontend/src/views/Materials.vue`
- Modify: `frontend/src/components/study/MaterialCard.vue`
- Modify: `frontend/src/styles.css`

- [ ] **Step 1: Compact table actions**

Operation column should use primary action plus accessible more menu. Deletion remains confirmed. Move/reindex actions from the frontend functional plan remain accessible from card and table.

- [ ] **Step 2: Contain overflow**

`.table-wrap` owns horizontal overflow; body must not get horizontal scroll at 360/390px. Cards use responsive minmax columns.

- [ ] **Step 3: Build**

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong\frontend"
npm run build
Pop-Location
```

Expected: PASS.

---

### Task 5: Chat responsive layout and accessibility

**Files:**
- Modify: `frontend/src/views/Chat.vue`
- Modify: `frontend/src/components/study/MessageBubble.vue`
- Modify: `frontend/src/components/study/EvidencePanel.vue`
- Modify: `frontend/src/styles.css`

- [ ] **Step 1: Desktop internal scroll**

At `>=1200px`, Chat uses three columns and internal scroll areas for conversation list, message pane, and evidence panel. Page body is not the transcript scroll container.

- [ ] **Step 2: Tablet/mobile controls**

Below `1200px`, expose `历史问答` and `学习范围与证据` controls with `aria-expanded`, opening drawer/sheet panels.

- [ ] **Step 3: Composer and status accessibility**

Composer uses autosize textarea, Ctrl/Cmd+Enter sends, Enter inserts newline, loading/timer statuses use `aria-live="polite"`.

- [ ] **Step 4: Long content wrapping**

Markdown/code/table content wraps or scrolls inside message/evidence containers without body-level horizontal scroll.

- [ ] **Step 5: Build**

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong\frontend"
npm run build
Pop-Location
```

Expected: PASS.

---

### Task 6: Profile compaction

**Files:**
- Modify: `frontend/src/views/Profile.vue`
- Modify: `frontend/src/styles.css`

- [ ] **Step 1: Compact current layout**

Keep existing features only: nickname, avatar URL, study goal, default question scope, answer style, evidence expanded preference, default task minutes, data/AI explanation.

- [ ] **Step 2: Improve density**

Use a profile-specific layout: account/avatar summary, two-column form rows on desktop, full-width study goal, compact local preferences, explanation card below or aside.

- [ ] **Step 3: Responsive rules**

Desktop two columns with tighter right column; below `768px` single column; below `390px` avatar row wraps and controls remain operable.

- [ ] **Step 4: Build**

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong\frontend"
npm run build
Pop-Location
```

Expected: PASS.

---

### Task 7: Dashboard visual/responsive hardening

**Files:**
- Modify: `frontend/src/views/Dashboard.vue`
- Modify: `frontend/src/components/study/MetricCard.vue`
- Modify: `frontend/src/styles.css`

- [ ] **Step 1: Metric and chart polish**

Dashboard metric icons use component icons; charts keep text summaries and accessible names. Focus/action cards have visible focus state independent of hover.

- [ ] **Step 2: Responsive grids**

Stat grid: 4 columns when wide enough, 2 columns around tablet, 1 column on mobile. Chart containers stay within page width at 360/390px.

- [ ] **Step 3: Build**

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong\frontend"
npm run build
Pop-Location
```

Expected: PASS.

---

### Task 8: Breakpoint and accessibility verification

**Files:**
- Verify: `frontend/src/styles.css`
- Verify: `frontend/src/components/AppLayout.vue`
- Verify: `frontend/src/views/Dashboard.vue`
- Verify: `frontend/src/views/Materials.vue`
- Verify: `frontend/src/views/Chat.vue`
- Verify: `frontend/src/views/Profile.vue`

- [ ] **Step 1: Build**

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong\frontend"
npm run build
Pop-Location
```

Expected: PASS.

- [ ] **Step 2: Manual responsive checks**

At widths `360`, `390`, `768`, `1024`, `1366`, `1440`, verify Dashboard, Plans, Materials, Chat, Profile:

```js
document.documentElement.scrollWidth <= document.documentElement.clientWidth
```

Expected: `true` for each target page; table overflow is allowed only inside `.table-wrap`.

- [ ] **Step 3: Manual accessibility checks**

Check:

- icon-only buttons have text, `aria-label`, or `title`.
- normal controls meet 44px hit target; compact table controls remain operable.
- keyboard can navigate nav, filters, cards, table actions, chat drawer buttons, composer, Profile forms, and Pomodoro controls.
- focus rings visible.
- drawer controls expose `aria-expanded`.
- charts include text summaries.
- reduced motion preference is respected.

## Final acceptance

- [ ] Shared Phase A tokens and focus styles exist.
- [ ] Structural Chinese glyph icons are replaced by SVG icon components.
- [ ] Navigation order is Dashboard, Plans, Materials, Chat, Profile.
- [ ] Buttons/input/icon controls are consistently sized and labelled.
- [ ] Profile is compact but not fully redesigned.
- [ ] Materials table/card and Chat are responsive without body horizontal scroll.
- [ ] `npm run build` passes.
