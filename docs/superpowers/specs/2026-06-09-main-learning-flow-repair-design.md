# Phase A 主学习链路修复设计方案

文档路径：`D:\学习资料\大数据综合实践\zonghexitong\docs\superpowers\specs\2026-06-09-main-learning-flow-repair-design.md`  
版本日期：2026-06-09  
适用项目：`D:\学习资料\大数据综合实践\zonghexitong`  
目标读者：实现者、产品/体验评审者、测试者、后续维护者

## 0. 结论

Phase A 修复当前个人学习助手的主学习链路，把它从“功能存在但容易断裂”的页面集合，整理成一个可靠的学习工作台：用户可以整理资料、观察索引重建状态、在持久 AI 会话中按学习范围追问、查看引用片段和完整资料、完成学习计划/清单、用轻量番茄钟记录每日学习时长，并在驾驶舱看到清晰的学习清单与可视化趋势。

Phase A 保留现有 Vue 3、Element Plus、ECharts、Pinia、Vue Router、Flask、JWT、SQLAlchemy、RAG/资料处理模块和当前应用形态。它不是重写平台，而是在现有架构内补齐主链路需要的窄范围持久状态、状态机、错误契约和视觉一致性。

Phase A 的验收路径是一句话：**用户能把未分类资料归类，移动资料后文件夹范围检索保持一致；能重建索引并看到 queued/running/succeeded/failed/cancelled/stale 状态；能在真实 AI 会话中继续、删除、重试并查看 Markdown 与引用；能在右侧面板看引用片段和完整资料；能完成番茄钟并在驾驶舱看到今日学习时长与趋势；全程没有图片空白、黑盒 500、聊天整页滚动、表格撑破页面或数据丢失。**

## 1. 背景与当前问题

当前系统已经具备资料上传、文件夹管理、资料详情、AI 问答、学习计划、今日任务、个人设置和统计仪表盘能力。但用户实际学习时遇到的主链路问题集中在这些地方：

1. **资料分类断点**：未分类资料无法重新归类；已分类资料也缺少清晰的“移动到文件夹”入口。
2. **索引反馈断点**：点击重建索引后没有可观察进度，只能等待；接口长时间占用时体验像卡死。
3. **资料管理表格断点**：操作按钮过多、表格宽度挤压、删除按钮与其它行按钮不齐。
4. **AI 会话断点**：会话不能删除；超时后后端返回 500，用户无法继续稳定对话。
5. **引用资产断点**：图片引用会出现 `/api/materials/assets/<id>/image` 404，前端没有清晰占位和恢复路径。
6. **学习范围断点**：学习范围和引用片段过长时超出边界，且学习范围每次都占据页面空间。
7. **聊天体验断点**：AI 回答以纯文本展示，Markdown 的 `**` 等符号裸露；输入框不会按内容增高；按钮和输入框尺寸不协调；页面整体滚动而不是面板内部滚动。
8. **驾驶舱断点**：信息太多、优先级混乱；用户看不到“今天先学什么”和“今天学了多久”。
9. **视觉系统断点**：按钮扁平、结构图标使用文字字形、Profile 卡片间距过大，整体不够像精致的学习工作台。

## 2. Phase A 范围边界

### 2.1 Must-have

Phase A 必须包含：

1. **资料库主链路修复**
   - 单个资料支持归类到文件夹、移动到其它文件夹、移回未分类。
   - `folder_id: null` 是公开 API 中唯一的未分类表示。
   - 卡片和表格都提供归类/移动入口。
   - 表格操作改为主操作加更多菜单，删除单独确认。

2. **索引重建可观察化**
   - `POST /api/materials/:id/reindex` 以 `202 Accepted` 返回 job/status。
   - `accepted` 只是 HTTP/UI 事件，不是持久状态；持久状态使用 `queued/running/succeeded/failed/cancelled/stale`。
   - 前端即时显示 job queued/running 状态并轮询。
   - 旧 ready 索引在新 generation 成功前保持可用，避免重建失败导致资料不可问。

3. **AI 会话工作台**
   - Phase A 纳入窄范围持久 `Conversation` / `Message` / `Citation` 能力，取代仅靠 `ChatHistory` 虚拟分组的方案。
   - 旧 `/api/chat` 与 `/api/chat/history` 通过迁移/适配保持可读。
   - 支持新建、切换、删除会话，失败消息可重试。
   - AI 超时保存失败 assistant 占位，返回稳定 `AI_TIMEOUT` 错误，不再让 UI 只看到黑盒 500。

4. **右侧资料面板**
   - 右侧支持 `引用片段`、`完整资料`、`学习范围` 三个区域。
   - 引用片段与完整资料都在内部滚动。
   - 学习范围默认按需展开，以 chip 表示当前范围。

5. **Markdown 与引用安全渲染**
   - AI 回答以不可信 Markdown 存储。
   - 前端使用 `markdown-it` + `DOMPurify` 或等价 parser/sanitizer 组合渲染。
   - 禁止危险 HTML、事件、脚本、iframe、危险 style、`javascript:` 链接。
   - 引用不混入任意 HTML，而作为结构化 citation 渲染。

6. **驾驶舱与计划顺序**
   - 驾驶舱采用“学习清单 + 可视化图表”融合版。
   - 首页优先显示今天先做什么、学习计划/今日清单、学习时长、任务趋势。
   - 学习计划在驾驶舱内容和导航顺序中位于资料库上方。

7. **轻量番茄钟与每日学习时长**
   - 新增 `FocusSession` 持久记录 completed 专注时长。
   - 番茄钟运行态、暂停态、重置态在 Phase A 为前端本地状态；后端只保存完成后的 session。
   - 驾驶舱展示今日学习时长和 7 天学习时长趋势。

8. **目标页面视觉修复**
   - `Dashboard`、`Materials`、`Chat`、`Plans`、`Profile` 与共享 study 组件使用统一视觉 token 和控件尺寸。
   - 结构图标从中文字形替换为 `@element-plus/icons-vue` 或批准的本地 SVG。
   - Chat 桌面端左/中/右内部滚动；移动端单列 + 抽屉/sheet。
   - Profile 只做布局收紧和对齐修复，不做完整个人中心重构。

### 2.2 Deferred / Phase B

这些内容不纳入 Phase A 必须验收：

- 完整 Profile 重新设计、复杂偏好系统、账号安全页。
- 全应用级大规模 design-system 重构；Phase A 只统一本轮触及页面和共享组件所需 token。
- 高级 dashboard 健康分析、AI 连续性深度洞察、导出、排名、复杂报表。
- 历史 `ChatHistory` 的完全编辑能力；Phase A 只保证旧记录可读并可迁移/适配为可删除会话。
- 文件夹 rename/delete 的全量历史 citation 回填；Phase A 保证 live SQL 显示和后续 RAG 查询不使用陈旧业务状态。
- 生产级分布式任务队列、跨进程 job 调度、跨设备番茄钟实时同步。
- 番茄钟历史补录、徽章、连续打卡、休息分析、任务强绑定。

### 2.3 Non-goals

Phase A 不做：

- 不替换 Vue 3、Element Plus、Flask、SQLAlchemy、数据库或路由体系。
- 不引入微服务、新认证/RBAC、多用户协作、公开分享、离线同步、支付、通知系统。
- 不整体重写 RAG/搜索系统。
- 不做错题本、闪卡、掌握度评分、间隔复习算法。
- 不做大型分析仓库或深度 BI。

## 3. 关键用户旅程

### 3.1 资料归类与范围一致

1. 用户进入资料库，切到“未分类”。
2. 在某个资料卡片或表格行点击“归类到文件夹”。
3. 选择已有文件夹，或新建文件夹后立即移动。
4. UI 显示行级 loading，成功后资料从“未分类”视图中消失。
5. 后端更新 SQL，并同步视觉资产 folder_id 与文本/视觉向量元数据。
6. 用户在该文件夹范围内问 AI，RAG 不再引用旧文件夹状态。

### 3.2 重建索引有反馈

1. 用户点击“重建索引”。
2. UI 立即显示“索引重建已开始”，按钮禁用并进入 loading。
3. 后端返回 `202 Accepted`、`job_id`、`generation`、`poll_url`。
4. 前端每 2 秒轮询 60 秒；之后每 5 秒轮询到 5 分钟；仍未完成时停止主动轮询并显示“仍在处理中，可稍后刷新”。
5. 成功后资料 `index_state=ready`，问 AI 按钮恢复。
6. 失败后显示 `error.message`、`retryable` 和重试入口。

### 3.3 AI 会话可继续、可删除、可重试

1. 用户新建会话或从资料页进入 `/chat?scope_type=material&material_id=...&prompt=...`。
2. 会话保存默认 scope；每条消息保存发送时的 scope snapshot。
3. 发送消息后，用户消息先持久化，assistant message 进入 `generating`。
4. AI 成功时 assistant message 变为 `succeeded`，并带 `citations`。
5. AI 超时时 assistant message 变为 `failed_timeout`，HTTP 返回 504 + `AI_TIMEOUT`，UI 显示“重试”。
6. 用户可继续输入新消息，也可重试失败消息。
7. 用户删除会话后，当前会话切换到最近会话或空状态，晚到的 AI 回复不会复活已删除会话。

### 3.4 引用片段与完整资料

1. AI 回答显示结构化引用入口。
2. 右侧面板默认展示当前 assistant message 的引用片段。
3. 点击引用可在右侧切到完整资料并定位相关片段或图片资产。
4. 图片加载失败时显示占位、caption、资料名和恢复路径。
5. 学习范围通过 chip 展示，用户点击才展开完整范围选择。

### 3.5 今日学习与番茄钟

1. 用户打开驾驶舱，看到今日学习清单、活跃计划、今日学习时长。
2. 用户启动番茄钟，支持开始、暂停、继续、重置。
3. 只有完成时前端提交 `POST /api/focus-sessions`。
4. 后端保存 completed `FocusSession`，驾驶舱刷新 `today_focus_seconds` 与 7 天学习时长趋势。
5. 未完成、重置、关闭浏览器前未提交的 session 不计入学习时长。

## 4. 实现触点

### 4.1 前端触点

- `D:\学习资料\大数据综合实践\zonghexitong\frontend\src\api\modules.js`
- `D:\学习资料\大数据综合实践\zonghexitong\frontend\src\api\http.js`
- `D:\学习资料\大数据综合实践\zonghexitong\frontend\src\components\AppLayout.vue`
- `D:\学习资料\大数据综合实践\zonghexitong\frontend\src\styles.css`
- `D:\学习资料\大数据综合实践\zonghexitong\frontend\src\views\Dashboard.vue`
- `D:\学习资料\大数据综合实践\zonghexitong\frontend\src\views\Materials.vue`
- `D:\学习资料\大数据综合实践\zonghexitong\frontend\src\views\MaterialDetail.vue`
- `D:\学习资料\大数据综合实践\zonghexitong\frontend\src\views\Chat.vue`
- `D:\学习资料\大数据综合实践\zonghexitong\frontend\src\views\Plans.vue`
- `D:\学习资料\大数据综合实践\zonghexitong\frontend\src\views\Profile.vue`
- `D:\学习资料\大数据综合实践\zonghexitong\frontend\src\components\study\MaterialCard.vue`
- `D:\学习资料\大数据综合实践\zonghexitong\frontend\src\components\study\EvidencePanel.vue`
- `D:\学习资料\大数据综合实践\zonghexitong\frontend\src\components\study\MessageBubble.vue`
- `D:\学习资料\大数据综合实践\zonghexitong\frontend\src\components\study\ScopeSelector.vue`
- `D:\学习资料\大数据综合实践\zonghexitong\frontend\src\components\study\VisualAssetGrid.vue`

Phase A 可新增聚焦组件：

- `D:\学习资料\大数据综合实践\zonghexitong\frontend\src\components\study\PomodoroTimer.vue`
- `D:\学习资料\大数据综合实践\zonghexitong\frontend\src\components\study\DashboardTopFusion.vue`
- `D:\学习资料\大数据综合实践\zonghexitong\frontend\src\components\study\DashboardPlanSection.vue`
- `D:\学习资料\大数据综合实践\zonghexitong\frontend\src\components\study\StudyDurationChart.vue`
- `D:\学习资料\大数据综合实践\zonghexitong\frontend\src\components\study\TodayChecklistPanel.vue`
- `D:\学习资料\大数据综合实践\zonghexitong\frontend\src\components\study\EChartPanel.vue`

### 4.2 后端触点

- `D:\学习资料\大数据综合实践\zonghexitong\backend\routes\materials.py`
- `D:\学习资料\大数据综合实践\zonghexitong\backend\routes\folders.py`
- `D:\学习资料\大数据综合实践\zonghexitong\backend\routes\chat.py`
- `D:\学习资料\大数据综合实践\zonghexitong\backend\routes\plans.py`
- `D:\学习资料\大数据综合实践\zonghexitong\backend\routes\tasks.py`
- `D:\学习资料\大数据综合实践\zonghexitong\backend\routes\stats.py`
- `D:\学习资料\大数据综合实践\zonghexitong\backend\models\material.py`
- `D:\学习资料\大数据综合实践\zonghexitong\backend\models\chat.py`
- `D:\学习资料\大数据综合实践\zonghexitong\backend\models\plan.py`
- `D:\学习资料\大数据综合实践\zonghexitong\backend\services\rag_service.py`
- `D:\学习资料\大数据综合实践\zonghexitong\backend\services\schema_service.py`
- `D:\学习资料\大数据综合实践\zonghexitong\backend\services\stats_service.py`
- `D:\学习资料\大数据综合实践\zonghexitong\backend\tests\`

Phase A 可新增：

- `D:\学习资料\大数据综合实践\zonghexitong\backend\models\focus.py`
- `D:\学习资料\大数据综合实践\zonghexitong\backend\routes\focus.py`
- chat conversation/message/citation 相关模型字段或表
- reindex job / generation 相关字段或表

## 5. Canonical 状态与枚举

本节是规范来源；其它章节使用这些词，不再引入同义状态。

| 对象 | 字段 | 值 | 说明 |
|---|---|---|---|
| Material | `status` | `uploaded`, `processing`, `ready`, `failed`, `deleted` | 兼容旧状态，用于粗粒度展示 |
| Material | `index_state` | `not_indexed`, `queued`, `running`, `ready`, `failed`, `stale` | 检索索引状态；`accepted` 不在这里 |
| ReindexJob | `status` | `queued`, `running`, `succeeded`, `failed`, `cancelled`, `stale` | job 状态；`stale` 表示被新 generation、删除或重启失效 |
| VisualAsset | `status` | `processing`, `ready`, `failed`, `missing_file`, `deleted` | 图片资产可用性 |
| Conversation | `status` | `active`, `deleted` | Phase A 使用 soft delete |
| Message | `status` | `pending`, `generating`, `succeeded`, `failed_timeout`, `failed_error`, `cancelled`, `deleted` | `role` 单独表示 user/assistant/system |
| Citation | `source_state` | `active`, `moved`, `reindexed`, `deleted`, `missing` | 引用来源状态 |
| FocusSession | `status` | `completed` | Phase A 只持久化 completed；running/paused 是前端本地状态 |
| StudyTask | `status` | `pending`, `done` | 保留现有任务状态语义 |
| Sync | `sync_state` | `synced`, `sync_pending`, `sync_failed` | SQL 与投影同步状态 |

状态转换：

- `ReindexJob`: `queued -> running -> succeeded|failed|cancelled|stale`。
- `Material.index_state`: `not_indexed|ready|failed|stale -> queued -> running -> ready|failed|stale`。
- `Message`: user message 保存后为 `succeeded`；assistant message `pending -> generating -> succeeded|failed_timeout|failed_error|cancelled`。
- `Conversation`: `active -> deleted`，不在 Phase A 做 restore。
- `FocusSession`: 后端只接收 completed payload 并保存为 `completed`。

## 6. Scope schema

`scope` 是发送 AI 消息和引用检索的规范上下文。

### 6.1 Allowed scope types

```json
{ "scope_type": "general" }
{ "scope_type": "all" }
{ "scope_type": "folder", "folder_id": 3 }
{ "scope_type": "uncategorized", "folder_id": null }
{ "scope_type": "material", "material_id": 12 }
```

规则：

- `general`：不要求资料引用，AI 可以泛化回答，右侧证据面板显示“本次未绑定资料证据”。
- `all`：检索当前用户所有 ready 资料。
- `folder`：`folder_id` 必须是当前用户拥有的数字 ID。
- `uncategorized`：公开表示为 `folder_id: null`，检索当前用户未分类且 ready 的资料。
- `material`：`material_id` 必须属于当前用户且 material `status=ready` 或存在上一代 ready index。

### 6.2 URL query mapping

`/chat?scope_type=material&material_id=12&prompt=...`：创建或打开草稿会话，预填 prompt，不自动发送。  
`/chat?scope_type=folder&folder_id=3`：使用 folder scope。  
`/chat?scope_type=uncategorized`：使用未分类 scope。  
无效 scope 返回或显示 `INVALID_SCOPE_TYPE`，并回退到 `all` 或要求用户重新选择；回退必须可见，不静默改变。

### 6.3 Scope snapshots

- 每条 message 保存 `scope_snapshot`。
- 用户中途切换 scope 只影响下一条消息。
- retry 默认使用失败消息原 `scope_snapshot`。
- material 被移动、删除或变为 not ready 后，旧消息的历史 scope 仍显示为 snapshot，但新检索使用当前 SQL 状态。

## 7. API 契约

### 7.1 统一 JSON 错误结构

触及的 JSON API 返回稳定错误结构：

```json
{
  "message": "AI 响应超时，请稍后重试",
  "error": {
    "code": "AI_TIMEOUT",
    "message": "AI 响应超时，请稍后重试",
    "details": {},
    "field_errors": {},
    "retryable": true,
    "request_id": "req_20260609_001"
  }
}
```

保留顶层 `message` 是为了兼容当前 `D:\学习资料\大数据综合实践\zonghexitong\frontend\src\api\http.js` 的错误展示。前端分支逻辑使用 `error.code`，不使用中文文案判断。

主要错误码：

- `VALIDATION_ERROR`
- `NOT_FOUND`
- `MATERIAL_NOT_FOUND`
- `MATERIAL_NOT_READY`
- `INVALID_SCOPE_TYPE`
- `INDEX_JOB_IN_PROGRESS`
- `INDEX_FAILED`
- `VECTOR_SYNC_FAILED`
- `IMAGE_ASSET_NOT_FOUND`
- `IMAGE_FILE_MISSING`
- `AI_TIMEOUT`
- `UPSTREAM_AI_ERROR`
- `CONFLICT`

HTTP 映射：400 参数错误；401 未登录；404 不存在或跨用户访问；409 状态冲突；422 当前状态不允许操作；502 上游 AI 错误；504 AI 超时；500 未预期错误。

### 7.2 Endpoint matrix

#### Material move

`PATCH /api/materials/:id/folder`

Request:

```json
{
  "folder_id": 3,
  "request_id": "move_20260609_001"
}
```

Move to uncategorized:

```json
{
  "folder_id": null,
  "request_id": "move_20260609_002"
}
```

200 response:

```json
{
  "message": "资料已移动到文件夹",
  "changed": true,
  "sync_state": "synced",
  "material": {
    "id": 12,
    "folder_id": 3,
    "folder_name": "数据仓库",
    "status": "ready",
    "index_state": "ready"
  },
  "folder_counts": [
    { "folder_id": 3, "material_count": 5 },
    { "folder_id": null, "material_count": 2 }
  ]
}
```

Same-target move returns 200 with `changed: false` and `sync_state: "synced"`.

If SQL move succeeds but vector/visual metadata sync fails, response remains 200 because user-visible classification changed, but includes a warning state:

```json
{
  "message": "资料已移动，但索引同步失败，可重建索引修复检索范围",
  "changed": true,
  "sync_state": "sync_failed",
  "error_code": "VECTOR_SYNC_FAILED",
  "retryable": true,
  "material": { "id": 12, "folder_id": 3, "index_state": "stale" }
}
```

Errors: 404 `MATERIAL_NOT_FOUND` or permission-safe folder `NOT_FOUND`; 409 `CONFLICT` for deleted material or incompatible state.

#### Reindex start

`POST /api/materials/:id/reindex`

Request:

```json
{ "request_id": "reindex_20260609_001" }
```

202 response:

```json
{
  "message": "索引重建已开始",
  "job": {
    "job_id": 18,
    "material_id": 12,
    "generation": 5,
    "status": "queued",
    "started_at": null,
    "finished_at": null,
    "poll_url": "/api/materials/12/index-status"
  },
  "material": {
    "id": 12,
    "status": "processing",
    "index_state": "queued",
    "active_index_generation": 4,
    "building_index_generation": 5
  }
}
```

Duplicate while active returns 202 with the existing active job and `message: "索引重建已在进行中"`.

#### Reindex status

`GET /api/materials/:id/index-status`

200 response:

```json
{
  "material_id": 12,
  "status": "processing",
  "index_state": "running",
  "active_index_generation": 4,
  "building_index_generation": 5,
  "job": {
    "job_id": 18,
    "status": "running",
    "phase": "indexing_visual",
    "started_at": "2026-06-09T10:00:00Z",
    "finished_at": null,
    "progress": {
      "chunks_indexed": 15,
      "visual_assets_indexed": 2,
      "visual_assets_failed": 0
    },
    "last_error": null,
    "error_code": null,
    "retryable": false
  },
  "ask_ai_available": true,
  "ask_ai_uses_generation": 4
}
```

`ask_ai_available=true` during reindex only when a previous ready generation exists. If no ready generation exists, it is false until the new job succeeds.

Server restart limit: Phase A uses persisted job rows plus in-process execution. If the process restarts while a job is `queued` or `running`, the next status read marks that job `stale` with `retryable=true` and leaves previous ready generation active if one exists.

#### Image asset

`GET /api/materials/assets/:asset_id/image`

Success: binary image response with correct `Content-Type`, `Cache-Control: private`, and auth required.  
Failure: 401/403/404 may be binary-route specific; if JSON is returned, use the standard envelope with `IMAGE_ASSET_NOT_FOUND` or `IMAGE_FILE_MISSING`. Frontend blob clients convert all 401/403/404/decode failures into accessible placeholders and do not infinite-retry.

#### Conversation and messages

`GET /api/chat/conversations?page=1&limit=30` returns active conversations newest-first.

`POST /api/chat/conversations`

```json
{
  "title": "数据仓库复习",
  "default_scope": { "scope_type": "all" }
}
```

201 response includes `{ "conversation": { "id": 9, "status": "active", ... } }`.

`DELETE /api/chat/conversations/:id` returns 204 no body. It is soft delete. Deleted conversations are excluded from list and dashboard recent chats.

`GET /api/chat/conversations/:id/messages?page=1&limit=50` returns messages and their `citations`.

`POST /api/chat/conversations/:id/messages`

```json
{
  "content": "解释这张图和对应概念",
  "scope": { "scope_type": "material", "material_id": 12 },
  "request_id": "chat_20260609_001"
}
```

Success 201:

```json
{
  "conversation_id": 9,
  "user_message": { "id": 101, "role": "user", "status": "succeeded" },
  "assistant_message": {
    "id": 102,
    "role": "assistant",
    "status": "succeeded",
    "content": "## 核心解释\n...",
    "citations": []
  }
}
```

Timeout 504:

```json
{
  "message": "AI 响应超时，可重试或继续提问",
  "conversation_id": 9,
  "user_message": { "id": 101, "role": "user", "status": "succeeded" },
  "assistant_message": {
    "id": 102,
    "role": "assistant",
    "status": "failed_timeout",
    "retryable": true,
    "error_code": "AI_TIMEOUT"
  },
  "error": {
    "code": "AI_TIMEOUT",
    "message": "AI 响应超时，可重试或继续提问",
    "details": { "timeout_seconds": 90 },
    "field_errors": {},
    "retryable": true,
    "request_id": "chat_20260609_001"
  }
}
```

`POST /api/chat/messages/:id/retry` retries a failed assistant message. The id must be an assistant message with `failed_timeout` or `failed_error`. It creates a new assistant attempt linked by `retry_of_message_id`. Duplicate `request_id` returns the existing attempt/result.

Returned field name is `citations`. Legacy endpoints may also expose `references` as an alias for backward compatibility.

#### Focus sessions

`POST /api/focus-sessions`

```json
{
  "client_session_id": "pomo_20260609_abc123",
  "started_at": "2026-06-09T09:00:00+08:00",
  "ended_at": "2026-06-09T09:25:00+08:00",
  "duration_seconds": 1500,
  "planned_seconds": 1500,
  "study_date": "2026-06-09",
  "timezone_offset_minutes": -480,
  "source": "pomodoro"
}
```

Validation:

- `duration_seconds` must be between 60 and 14400.
- If timestamps are supplied, server verifies duration is within 5 seconds of computed duration.
- `client_session_id` is unique per user. Duplicate returns 200 with the existing session and does not double-count.
- Cross-midnight sessions count on `study_date`, which is the browser local completion date sent by the frontend.

201 response:

```json
{
  "focus_session": {
    "id": 7,
    "client_session_id": "pomo_20260609_abc123",
    "status": "completed",
    "duration_seconds": 1500,
    "study_date": "2026-06-09",
    "source": "pomodoro"
  },
  "today_focus_seconds": 3000
}
```

#### Dashboard and trends

`GET /api/stats/dashboard` returns:

```json
{
  "generated_at": "2026-06-09T10:00:00Z",
  "today_focus_seconds": 3000,
  "today_checklist": {
    "items": [],
    "total": 0,
    "done": 0,
    "overdue": 0
  },
  "active_plan_summary": null,
  "next_actions": [],
  "task_trend": [],
  "focus_duration_trend": [],
  "material_type_summary": [],
  "folder_summary": [],
  "knowledge_health": {},
  "ai_continuity": {}
}
```

Arrays for 7-day charts are zero-filled for days without data. Empty states use empty arrays or null summaries, not missing fields.

`GET /api/stats/focus-duration-trend?days=7` returns:

```json
[
  { "date": "2026-06-03", "duration_seconds": 0 },
  { "date": "2026-06-04", "duration_seconds": 1800 }
]
```

`days` accepts 1–30; default 7.

## 8. 资料库与索引设计

### 8.1 归类/移动 UX

资料卡片和表格行都新增单资料操作：

- 未分类资料显示“归类到文件夹”。
- 已分类资料显示“移动到文件夹”。
- 目标可选已有文件夹，也可新建文件夹后立即移动。
- 目标可选“未分类”，表示移回 `folder_id: null`。
- 当前目标与原 folder 相同则确认按钮禁用。
- 成功后以后端返回资料对象为 UI 真相，刷新 folder counts 和当前列表。
- 如果资料移出当前筛选范围，从当前视图中移除。

表格中只保留主操作，次要操作进更多菜单。更多菜单必须可键盘访问，不依赖 hover。删除操作保留确认。

### 8.2 Folder rename/delete reconciliation

Phase A 最小规则：

- Folder rename 后，SQL 中的 folder name 是展示真相；后续 RAG 返回前用 SQL current name 覆盖 live display name。
- Folder delete 后，所属 material 变为 `folder_id: null`，并触发或标记向量 metadata sync。
- 历史 citation 的 `folder_name_snapshot` 不强制回填；它用于说明回答时的历史上下文。live material 打开时显示当前 SQL 名称。
- 如果向量 folder metadata 无法同步，受影响 material `index_state=stale` 或 `sync_state=sync_failed`，UI 提供重建索引。

### 8.3 RAG 元数据一致性

资料移动、文件夹重命名、文件夹删除、重建索引都必须维护一致性：

- `Material.folder_id`
- `MaterialVisualAsset.folder_id`
- 文本 chunk 的向量 metadata
- 视觉资产的向量 metadata
- live retrieval scope cache
- citation display rules

RAG 返回引用前，后端要用 SQL 验证：当前用户拥有该 material/asset、material 未删除、material 当前 folder 与 scope 兼容、asset 状态可用或返回结构化 unavailable 状态。

### 8.4 索引执行模型

Phase A 使用轻量执行模型：持久 `ReindexJob` 行 + 应用进程内后台执行。它不是生产级分布式队列。限制：进程重启时 running job 标记为 `stale`，用户可重新触发；旧 ready generation 继续可用。

Two-generation rule：

- `active_index_generation` 是当前可检索 generation。
- `building_index_generation` 是正在构建的 generation。
- 新 generation 成功前不替换 active generation。
- 新 generation 成功后切换 active generation，再清理旧向量。
- 失败不会移除旧可用索引。

## 9. AI 会话设计

### 9.1 信息架构

桌面端三块区域：

```text
左侧 Conversations | 中间 Chat Transcript + Composer | 右侧 Context Panel
```

- 左侧：会话列表、新建会话、删除会话、最近预览。
- 中间：消息流、Markdown 气泡、失败/重试、复制、输入框。
- 右侧：引用片段、完整资料、学习范围。

桌面端 Chat workbench 使用 viewport-bounded 高度，三个区域内部滚动。页面 body 不是聊天消息滚动容器。

移动端不强制三列：单列消息流优先；会话列表用 drawer/sheet；引用和学习范围用 tab/sheet/折叠面板；无 body 级横向滚动。

### 9.2 ChatHistory compatibility

Phase A 选择 **迁移优先，适配兜底**：

1. schema migration 或首次读取时，把每条旧 `ChatHistory` 转成一个 Conversation，包含 user message 与 assistant message。
2. 转换后的 conversation 可删除。
3. 若迁移失败，旧 `/api/chat/history` 仍可读，但新 UI 显示 legacy warning，并允许用户从旧问答“继续为新会话”。
4. Dashboard chat counts 使用 active Conversation 统计；未迁移 legacy rows 只在 legacy history 统计中保留。

### 9.3 Conversation 行为

- 支持显式“新建会话”。
- 从资料页进入 chat 时创建或打开草稿会话，预填 prompt，不强制自动发送。
- title 使用首条用户消息自动生成；失败时使用时间或“新会话”。
- 会话列表最近优先，分页默认 limit 30。
- 删除会话需要确认；采用 soft delete；DELETE 返回 204。
- 删除当前会话后切到最近 active 会话；没有会话则显示空状态。
- in-flight 回复晚到时检查 conversation 是否 deleted，deleted 则不复活。

### 9.4 Message 行为

发送规则：

1. 先保存 user message，`role=user`、`status=succeeded`。
2. 创建 assistant message，`role=assistant`、`status=generating`。
3. 调用 RAG 和 AI。
4. 成功后 assistant `status=succeeded`，保存 Markdown 内容与 `citations`。
5. 超时后 assistant `status=failed_timeout`，HTTP 504 + `AI_TIMEOUT`。
6. 上游失败 assistant `status=failed_error`，HTTP 502 + `UPSTREAM_AI_ERROR`。
7. 重试创建新的 assistant message，`retry_of_message_id` 指向原失败 message。

Composer 行为：

- 发送中禁用当前 send 按钮，但失败消息不阻塞后续新消息。
- draft 文本在超时/失败时保留，除非 user message 已成功提交；若已提交，composer 清空但失败 assistant 显示 retry。
- Ctrl/Cmd + Enter 发送；Enter 换行，并在 UI 显示提示。

### 9.5 Citation schema

Citation 字段：

```json
{
  "id": 1,
  "type": "text",
  "material_id": 12,
  "material_title_snapshot": "数据仓库讲义",
  "folder_id_snapshot": 3,
  "folder_name_snapshot": "数据仓库",
  "chunk_id": 88,
  "chunk_index": 4,
  "asset_id": null,
  "page_number": 3,
  "asset_index": null,
  "caption": null,
  "preview": "事实表围绕业务过程建立...",
  "score": 0.82,
  "score_display": "相关度 82%",
  "source_state": "active",
  "generation": 4
}
```

`score` 可存储原始浮点值，前端显示时四舍五入为百分比；如果 retrieval 不返回 score，则 `score` 和 `score_display` 为 null。

Citation UX：以 assistant message 为单位展示；默认显示最新有引用的 assistant message；文本预览默认 3–4 行；图片预览不裁剪；引用来源已删除或失效时回答仍可见，引用卡片显示 source state 和恢复路径。

### 9.6 Markdown 安全渲染

允许：段落、标题、有序/无序列表、引用块、链接、行内代码、代码块、表格。  
禁止：raw HTML、script、iframe、事件属性、style 属性、`javascript:`/`data:` 协议链接。  
外部链接添加 `target="_blank" rel="noopener noreferrer"`。  
测试 payload 至少包括 `<script>`, `<img onerror>`, `<a href="javascript:...">`, `<iframe>`, style 注入。

## 10. 驾驶舱、计划与番茄钟设计

### 10.1 Dashboard 信息层级

Dashboard 分为四个区域：

1. 顶部驾驶舱：今日先做什么、今日已专注多久、下一步行动、番茄钟入口。
2. 学习计划 / 今日清单：位于资料库模块上方；最多展示 5 个行动任务；无计划显示“新建计划”。
3. 学习节奏图表：7 天学习时长柱状图、任务完成趋势、文字摘要。
4. 资料与 AI 线索：资料类型、知识健康、文件夹分布、AI 连续性降级为紧凑信息或下方卡片。

### 10.2 导航顺序

```text
驾驶舱
学习计划
资料库
AI 会话
个人设置
```

导航使用统一 SVG 图标并保留文字标签。当前状态不只靠颜色，还使用 pill、rail、边框或字重表示。

### 10.3 FocusSession

Phase A 后端只保存 completed session。前端 timer 的 running、paused、reset 不跨设备同步。

字段：`id`, `user_id`, `started_at`, `ended_at`, `duration_seconds`, `planned_seconds`, `study_date`, `source`, `status`, `client_session_id`, `created_at`。

规则：

- `duration_seconds` 60–14400。
- `client_session_id` 对同一 user 唯一；重复提交返回已有记录。
- `study_date` 是浏览器本地完成日期；后端保存该日期和 timezone offset。
- 跨午夜按 completion `study_date` 计入。
- Phase A 不从聊天或阅读行为推断学习时长。

## 11. 视觉系统与布局

### 11.1 Token 范围

Phase A 只统一本轮触及页面和共享 study 组件所需 token，不做全应用视觉重构。`D:\学习资料\大数据综合实践\zonghexitong\frontend\src\styles.css` 增加或整理：surface、border、text、muted text、primary、success、warning、danger、focus ring、radius、elevation、spacing、icon size、z-index、motion 150–300ms。

### 11.2 Buttons and controls

- 常规按钮点击区域不少于 44px。
- 图标按钮 44×44px。
- 相邻按钮间距不少于 8px。
- 表格紧凑按钮视觉高度可为 36–40px，但可点击区域仍需满足可访问性。
- Primary/secondary/danger 层级清晰。
- hover、pressed、focus-visible、loading、disabled 都有可见状态。

### 11.3 Icons

替换结构性中文字形图标：`今`, `库`, `问`, `划`, `我`, `册`, `文`, `图`, `待`, `✓`, `!`。统一使用 `@element-plus/icons-vue` 或批准的本地 SVG。中文文字可作为品牌标识或可见 label，但不作为结构图标。

### 11.4 Chat breakpoints

- `>= 1200px`：三列常驻，左/中/右内部滚动。
- `768px–1199px`：中间 Chat 为主，Conversations 和 Context 可折叠为侧边 drawer 或 tabbed panel。
- `< 768px`：单列 message + composer，Conversations 和 Context 使用 sheet/drawer；无 body 横向滚动。

桌面 workbench 使用 `height: calc(100dvh - header - page padding)`，`overflow: hidden`，grid/flex 子项 `min-height: 0`。发送消息只滚动 message pane。

### 11.5 Materials and Profile

Materials：小屏默认卡片；表格模式是显式管理模式；表格 overflow 限制在 `.table-wrap`；操作列为主操作 + 更多菜单。

Profile：Phase A 仅收紧稀疏大卡片，头像/账户信息为主卡，学习偏好用紧凑 fieldset 或卡片，数据与 AI 说明降级为说明卡或折叠说明，表单最大宽度受控。

## 12. 迁移、兼容与并发

### 12.1 迁移与兼容

- 保留现有 materials、folders、plans、tasks、visual assets。
- `ChatHistory` 采用迁移优先、适配兜底策略。
- 保留 localStorage 偏好，例如 `studyhub.defaultScope`。
- 新 schema 采用非破坏性迁移和默认值 backfill。
- 开发/测试数据库可以重建；用户数据数据库不得靠 reset 完成迁移。

### 12.2 并发与幂等

- 所有 id 写操作必须按 JWT user 隔离。
- 跨用户访问返回安全 404。
- 同一资料重复 reindex coalesce 或 idempotent。
- 删除资料会 cancel/ignore in-flight index job。
- 资料移动与 reindex 使用 generation guard，旧 job 不覆盖新状态。
- chat send/retry 使用 `request_id` 或 failed message id 去重。
- 删除会话后 in-flight reply 不复活。
- focus session 使用 `client_session_id` 避免重复计数。

### 12.3 日志与观测

记录但不泄露敏感内容：reindex enqueue/complete/fail、vector sync fail、image file missing、AI timeout/upstream failure、chat retry、focus session duplicate submission。日志不得包含完整用户 prompt、资料正文或敏感文件路径。

## 13. 测试与验收

### 13.1 后端测试

新增或扩展 `D:\学习资料\大数据综合实践\zonghexitong\backend\tests`：

资料与索引：未分类移入文件夹、已分类移动、移回 `folder_id:null`、同目标 no-op、跨用户拒绝、sync_failed partial success、folder rename/delete live SQL display、reindex 202、重复 reindex、stale generation、delete during job、partial text/visual failure、image row missing、image file missing、stale citation asset。

AI 会话：ChatHistory migration/adapter、conversation create/list/delete、message send/list、AI timeout 保存 `failed_timeout`、retry failed message、delete while answer pending、citation payload shape、malformed historical references、idempotent request_id。

番茄钟与驾驶舱：FocusSession create、duration validation、duplicate client_session_id、today_focus_seconds、7-day zero-filled trend、cross-user access、dashboard snapshot fields stable。

### 13.2 前端/手工验证

- Materials card/table move actions and row loading。
- Uncategorized row disappears after classification。
- Reindex queued/running/succeeded/failed/stale UI and polling cleanup on unmount。
- Image 404 placeholder with accessible copy and recovery action。
- Chat create/delete/switch/retry/copy/scope/citation interactions。
- Markdown rendering and XSS smoke payloads do not execute。
- Desktop Chat internal scroll; mobile sheet/drawer behavior。
- Dashboard plan section above materials; charts loading/empty/error; focus duration refresh。
- Pomodoro keyboard controls, live-region status, reduced-motion behavior。
- Profile compact layout and avatar fallback。

### 13.3 响应式与可访问性

Verify at 360/390px, 768px, 1024px, 1366/1440px:

- no body-level horizontal scroll;
- table overflow only inside table wrapper;
- icon-only controls have `aria-label`;
- navigation icons have visible labels;
- disclosures/drawers/scope controls use `aria-expanded`;
- chat loading/error/timer status use polite `aria-live`;
- focus rings are visible;
- keyboard can complete navigation, filtering, sending, retrying, copying, deleting, scope switching, and Pomodoro controls;
- charts include text summaries;
- reduced motion disables or reduces non-essential animation;
- normal text contrast meets WCAG AA 4.5:1, large/icon contrast at least 3:1.

### 13.4 执行命令

Back end:

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong\backend"
python -m pytest tests
Pop-Location
```

Front end:

```powershell
Push-Location "D:\学习资料\大数据综合实践\zonghexitong\frontend"
npm run build
Pop-Location
```

If frontend unit/e2e test scripts are added later, the implementation plan should add the exact commands before final verification.

## 14. Risk register

| 风险 | 缓解 |
|---|---|
| Scope 过大 | Must-have 与 Deferred 已分开；Phase A 只围绕主链路 |
| 向量元数据与 SQL 不一致 | SQL canonical；向量为投影；move/rename/delete/reindex 统一 sync 或 stale 状态 |
| Reindex 长时间运行 | 202 + job + poll；旧 ready 索引保留到新 generation 成功 |
| AI 超时导致会话损坏 | 先持久化用户消息和 assistant generating；失败转 failed_timeout；retry idempotent |
| 图片 404 破坏引用体验 | 后端区分 asset missing/file missing；前端 blob fallback 和占位 |
| Markdown XSS | parser + sanitizer；禁止 raw HTML 和危险协议；XSS smoke tests |
| Chat 内部滚动影响移动端 | 桌面 viewport-bounded；移动端单列 + drawer/sheet |
| 番茄钟重复计数 | `client_session_id` 去重；只统计 completed session |
| 迁移破坏旧数据 | 非破坏性 schema/backfill；ChatHistory migration/adapter |

## 15. Phase A 最终验收清单

- [ ] 未分类资料可归类到文件夹。
- [ ] 已分类资料可移动到其它文件夹或移回未分类。
- [ ] 资料移动后文件夹范围 RAG 不引用旧 folder 元数据。
- [ ] 重建索引返回 job，前端可观察 queued/running/succeeded/failed/cancelled/stale。
- [ ] 重建失败有明确原因和重试路径。
- [ ] 资料表格不撑破页面，操作按钮对齐，删除在可访问更多菜单中确认。
- [ ] 图片引用失败时显示占位、来源信息和恢复路径。
- [ ] AI 会话可新建、切换、删除。
- [ ] AI 超时后会话仍可继续，失败消息可重试。
- [ ] Markdown 安全渲染，长代码/表格不撑破页面，XSS payload 不执行。
- [ ] 右侧资料面板可查看引用片段、完整资料、学习范围。
- [ ] 学习范围默认按需展开。
- [ ] Chat 桌面端左/中/右内部滚动，页面不作为消息滚动容器。
- [ ] 驾驶舱优先显示今日清单、学习计划、学习时长和图表。
- [ ] 学习计划在资料库模块上方，导航顺序为驾驶舱、学习计划、资料库、AI 会话、个人设置。
- [ ] 番茄钟完成后保存 FocusSession，并更新今日学习时长。
- [ ] 导航使用统一 SVG 图标，不再用中文字形作为结构图标。
- [ ] 按钮、输入框、卡片、Profile 布局使用统一视觉 token 和可访问尺寸。
- [ ] 360/390px、768px、1024px、1366/1440px 均无 body 横向滚动。
- [ ] 后端 `python -m pytest tests` 与前端 `npm run build` 通过。

## 16. 与 2026-06-08 旧 redesign spec 的关系

`D:\学习资料\大数据综合实践\zonghexitong\docs\superpowers\specs\2026-06-08-personal-learning-system-redesign-design.md` 曾把真实 `ChatConversation` / `ChatMessage` 持久化模型推迟到后续阶段。Phase A 主链路修复设计已根据当前用户反馈更新该决定：**本次 Phase A 包含窄范围持久 Conversation/Message/Citation，用于会话删除、继续对话、超时恢复、引用快照和右侧资料面板。**

该更新不等于完整平台化重构；它只补齐当前主学习链路所需的最小持久状态。旧 spec 中关于温暖学习工作台、Dashboard/Materials/Plans/Profile 方向仍可作为视觉和产品背景参考，但本文件是 2026-06-09 主学习链路修复的实施依据。
