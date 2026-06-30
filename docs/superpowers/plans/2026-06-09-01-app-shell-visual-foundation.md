# App Shell and Visual Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish the visible workbench foundation that every later user flow relies on: stable JSON error handling, navigation order, real icons, shared tokens, and accessible control sizing.

**Architecture:** Keep the existing Vue 3 + Element Plus layout and make narrow foundation changes in the app shell and global CSS. The HTTP client preserves the current top-level `message` compatibility while exposing stable `error.code` metadata to later flows.

**Tech Stack:** Vue 3, Vue Router, Pinia, Element Plus, `@element-plus/icons-vue`, Axios, Vite.

---

## Scope and dependencies

**User-flow position:** First visible frame after login: sidebar, topbar, app content shell, and global controls.

**Depends on:** None.

**Independently testable value:** After this plan, the app builds, the navigation order is `驾驶舱 -> 学习计划 -> 资料库 -> AI 会话 -> 个人设置`, structural icons are SVG components instead of Chinese glyphs, shared touched-page tokens exist, and API failures expose stable error metadata for later plans.

## File structure

- Modify: `D:\学习资料\大数据综合实践\zonghexitong\frontend\package.json`
  - Keep dependency declarations explicit for libraries used by this Phase A plan suite.
- Modify: `D:\学习资料\大数据综合实践\zonghexitong\frontend\src\api\http.js`
  - Normalize response errors into `{ message, code, retryable, details, fieldErrors, requestId, status }` while preserving Element Plus toast behavior.
- Modify: `D:\学习资料\大数据综合实践\zonghexitong\frontend\src\components\AppLayout.vue`
  - Reorder nav items and replace structural Chinese glyph icons with Element Plus icon components.
- Modify: `D:\学习资料\大数据综合实践\zonghexitong\frontend\src\styles.css`
  - Add scoped Phase A visual tokens, focus rings, minimum hit areas, surface tokens, layout overflow protections, and reduced-motion support used by touched pages.

## Tasks

### Task 1: Add Phase A dependency declarations

**Files:**
- Modify: `D:\学习资料\大数据综合实践\zonghexitong\frontend\package.json`

- [ ] **Step 1: Update dependency list**

Add these dependencies under `dependencies` if they are not already present. Keep existing versions unchanged for existing packages.

```json
{
  "dependencies": {
    "@element-plus/icons-vue": "^2.3.1",
    "@vitejs/plugin-vue": "^5.1.4",
    "axios": "^1.7.7",
    "dompurify": "^3.1.7",
    "echarts": "^5.5.1",
    "element-plus": "^2.8.4",
    "markdown-it": "^14.1.0",
    "pinia": "^2.2.4",
    "vite": "^5.4.8",
    "vue": "^3.5.10",
    "vue-router": "^4.4.5"
  }
}
```

- [ ] **Step 2: Install dependency lock updates**

Run:

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong\frontend"
npm install
Pop-Location
```

Expected: `package-lock.json` updates and no install failure.

- [ ] **Step 3: Commit dependency foundation**

```powershell
git add "D:\学习资料\大数据综合实践\zonghexitong\frontend\package.json" "D:\学习资料\大数据综合实践\zonghexitong\frontend\package-lock.json"
git commit -m @'
chore: add workbench frontend dependencies

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
'@
```

### Task 2: Normalize API error metadata

**Files:**
- Modify: `D:\学习资料\大数据综合实践\zonghexitong\frontend\src\api\http.js`

- [ ] **Step 1: Replace the HTTP client implementation with an error normalizer**

Use this structure so later plans can branch on `apiError.code` instead of Chinese message text.

```js
import axios from 'axios'
import { ElMessage } from 'element-plus'

import { useAuthStore } from '../stores/auth'

const http = axios.create({
  baseURL: '/api',
  timeout: 90000
})

export function normalizeApiError(error) {
  const data = error.response?.data || {}
  const envelope = data.error || {}
  return {
    message: envelope.message || data.message || '请求失败，请稍后重试',
    code: envelope.code || data.error_code || 'UNKNOWN_ERROR',
    retryable: Boolean(envelope.retryable || data.retryable),
    details: envelope.details || {},
    fieldErrors: envelope.field_errors || {},
    requestId: envelope.request_id || data.request_id || '',
    status: error.response?.status || 0,
    raw: data
  }
}

http.interceptors.request.use((config) => {
  const auth = useAuthStore()
  if (auth.token) {
    config.headers.Authorization = `Bearer ${auth.token}`
  }
  return config
})

http.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const apiError = normalizeApiError(error)
    error.apiError = apiError
    ElMessage.error(apiError.message)
    if (apiError.status === 401) {
      const auth = useAuthStore()
      auth.logout()
    }
    return Promise.reject(error)
  }
)

export default http
```

- [ ] **Step 2: Run frontend build**

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong\frontend"
npm run build
Pop-Location
```

Expected: Vite build succeeds with no unresolved import errors.

### Task 3: Replace structural navigation glyphs with SVG icons and reorder navigation

**Files:**
- Modify: `D:\学习资料\大数据综合实践\zonghexitong\frontend\src\components\AppLayout.vue`

- [ ] **Step 1: Update icon imports**

Replace the existing icon import with:

```js
import {
  ChatDotRound,
  Collection,
  DataBoard,
  Files,
  Setting,
  SwitchButton
} from '@element-plus/icons-vue'
```

- [ ] **Step 2: Update nav item order**

Replace `navItems` with:

```js
const navItems = [
  { path: '/dashboard', label: '今日驾驶舱', icon: DataBoard },
  { path: '/plans', label: '学习计划', icon: Collection },
  { path: '/materials', label: '知识库', icon: Files },
  { path: '/chat', label: 'AI 学习会话', icon: ChatDotRound },
  { path: '/profile', label: '个人设置', icon: Setting }
]
```

- [ ] **Step 3: Render icon components**

Replace this template fragment:

```vue
<span class="nav-icon" aria-hidden="true">{{ item.icon }}</span>
```

with:

```vue
<span class="nav-icon" aria-hidden="true">
  <component :is="item.icon" />
</span>
```

- [ ] **Step 4: Verify keyboard-visible navigation**

Run:

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong\frontend"
npm run build
Pop-Location
```

Expected: build succeeds. Manual check at `/dashboard`: tab focus reaches every nav item in the specified order and each item still shows a visible text label.

### Task 4: Add shared Phase A visual tokens and hit-area rules

**Files:**
- Modify: `D:\学习资料\大数据综合实践\zonghexitong\frontend\src\styles.css`

- [ ] **Step 1: Add token block near the top of the file**

Add or merge this block under existing `:root` rules. If a token already exists with the same name, keep the stronger existing brand value but preserve every variable name below.

```css
:root {
  --surface-page: #fbf7ef;
  --surface-card: #fffdf8;
  --surface-card-muted: #f7efe1;
  --surface-elevated: #ffffff;
  --border-soft: #eadcc7;
  --border-strong: #d8c4a4;
  --text-main: #2a2118;
  --text-muted: #756958;
  --text-subtle: #9a8b76;
  --color-primary: #2f80ed;
  --color-primary-strong: #1d5fbf;
  --color-success: #2f9e44;
  --color-warning: #f08c00;
  --color-danger: #d9480f;
  --focus-ring: 0 0 0 3px rgba(47, 128, 237, 0.24);
  --radius-sm: 10px;
  --radius-md: 16px;
  --radius-lg: 24px;
  --shadow-soft: 0 12px 36px rgba(87, 62, 32, 0.10);
  --shadow-lifted: 0 18px 48px rgba(87, 62, 32, 0.16);
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;
  --icon-size-md: 20px;
  --hit-area: 44px;
  --motion-fast: 150ms ease;
  --motion-medium: 240ms ease;
  --z-drawer: 2000;
}
```

- [ ] **Step 2: Add shared focus and control sizing rules**

Add these rules once, after base element styles:

```css
button,
.el-button,
.el-input__wrapper,
.el-textarea__inner,
.el-select .el-select__wrapper {
  transition: border-color var(--motion-fast), box-shadow var(--motion-fast), transform var(--motion-fast), background var(--motion-fast);
}

.el-button {
  min-height: var(--hit-area);
  border-radius: 999px;
  font-weight: 700;
}

.el-button.is-circle,
.icon-button {
  width: var(--hit-area);
  min-width: var(--hit-area);
  height: var(--hit-area);
}

.el-button + .el-button,
.el-button + .el-dropdown,
.el-dropdown + .el-button {
  margin-left: var(--space-2);
}

:focus-visible,
.el-button:focus-visible,
.nav-link:focus-visible,
.history-item:focus-visible,
.action-card:focus-visible {
  outline: none;
  box-shadow: var(--focus-ring);
}
```

- [ ] **Step 3: Add overflow and reduced-motion safeguards**

```css
.content,
.panel,
.workbench-panel,
.table-wrap,
.chat-workbench,
.messages,
.evidence-list {
  min-width: 0;
}

.table-wrap {
  overflow-x: auto;
  max-width: 100%;
}

img,
svg,
canvas {
  max-width: 100%;
}

@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.001ms !important;
    animation-iteration-count: 1 !important;
    scroll-behavior: auto !important;
    transition-duration: 0.001ms !important;
  }
}
```

- [ ] **Step 4: Build and manually verify the foundation**

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong\frontend"
npm run build
Pop-Location
```

Expected: build succeeds. Manual checks at 390px and 1366px: no body-level horizontal scroll on `/dashboard`, sidebar nav labels remain visible on desktop, focus rings are visible on keyboard navigation.

### Task 5: Commit visual foundation

**Files:**
- Modify: `D:\学习资料\大数据综合实践\zonghexitong\frontend\src\api\http.js`
- Modify: `D:\学习资料\大数据综合实践\zonghexitong\frontend\src\components\AppLayout.vue`
- Modify: `D:\学习资料\大数据综合实践\zonghexitong\frontend\src\styles.css`

- [ ] **Step 1: Review diff for forbidden structural glyphs**

Run:

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong"
git diff -- "frontend/src/components/AppLayout.vue" "frontend/src/styles.css" "frontend/src/api/http.js"
Pop-Location
```

Expected: no `icon: '今'`, `icon: '库'`, `icon: '问'`, `icon: '划'`, or `icon: '我'` remains in `AppLayout.vue`.

- [ ] **Step 2: Commit**

```powershell
git add "D:\学习资料\大数据综合实践\zonghexitong\frontend\src\api\http.js" "D:\学习资料\大数据综合实践\zonghexitong\frontend\src\components\AppLayout.vue" "D:\学习资料\大数据综合实践\zonghexitong\frontend\src\styles.css"
git commit -m @'
feat: establish learning workbench shell foundation

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
'@
```

## Final verification for this plan

Run:

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong\frontend"
npm run build
Pop-Location
```

Expected: build succeeds. Manual acceptance: navigation order matches the Phase A spec, structural icons are SVG components, touched controls have visible focus rings and minimum 44px hit areas, and failed API responses expose `error.apiError.code` for later flows.
