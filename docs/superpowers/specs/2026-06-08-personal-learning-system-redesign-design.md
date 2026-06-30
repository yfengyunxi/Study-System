# 个人学习系统重新设计方案

版本日期：2026-06-08  
项目定位：以今日学习为入口的温暖 AI 学习工作台  
最低可交付范围：以现有接口兼容为前提完成 Phase 1，并只加入 Phase 2 中明确列出的轻量字段、筛选与校验；Phase 3 以后均为单独里程碑，不纳入本轮必须验收。

## 参考当前代码路径

本方案基于当前项目结构整理，关键实现入口包括：

- `D:\学习资料\大数据综合实践\zonghexitong\frontend\src\components\AppLayout.vue`
- `D:\学习资料\大数据综合实践\zonghexitong\frontend\src\styles.css`
- `D:\学习资料\大数据综合实践\zonghexitong\frontend\src\router\index.js`
- `D:\学习资料\大数据综合实践\zonghexitong\frontend\src\api\modules.js`
- `D:\学习资料\大数据综合实践\zonghexitong\frontend\src\views\Dashboard.vue`
- `D:\学习资料\大数据综合实践\zonghexitong\frontend\src\views\Materials.vue`
- `D:\学习资料\大数据综合实践\zonghexitong\frontend\src\views\MaterialDetail.vue`
- `D:\学习资料\大数据综合实践\zonghexitong\frontend\src\views\Chat.vue`
- `D:\学习资料\大数据综合实践\zonghexitong\frontend\src\views\Plans.vue`
- `D:\学习资料\大数据综合实践\zonghexitong\frontend\src\views\Profile.vue`
- `D:\学习资料\大数据综合实践\zonghexitong\backend\models\chat.py`
- `D:\学习资料\大数据综合实践\zonghexitong\backend\models\material.py`
- `D:\学习资料\大数据综合实践\zonghexitong\backend\models\plan.py`
- `D:\学习资料\大数据综合实践\zonghexitong\backend\routes\chat.py`
- `D:\学习资料\大数据综合实践\zonghexitong\backend\routes\materials.py`
- `D:\学习资料\大数据综合实践\zonghexitong\backend\routes\folders.py`
- `D:\学习资料\大数据综合实践\zonghexitong\backend\routes\plans.py`
- `D:\学习资料\大数据综合实践\zonghexitong\backend\routes\tasks.py`
- `D:\学习资料\大数据综合实践\zonghexitong\backend\services\stats_service.py`

## 已批准决策清单

### 必须保留

- 保留暖色学习手账风格，避免改成冷色企业后台。
- 保留 Vue 3、Element Plus、ECharts、Pinia、Vue Router、Flask、JWT、SQLAlchemy 技术栈。
- 保留现有认证流程、登录注册页面、路由守卫和受保护页面结构。
- 保留现有路由：`/dashboard`、`/materials`、`/materials/:id`、`/chat`、`/plans`、`/plans/:id`、`/profile`。
- 保留现有主要接口兼容：`POST /api/chat`、`GET /api/chat/history`、`GET /api/tasks/today`、`GET /api/plans`、`GET /api/materials`。

### 必须新增或改造

- Dashboard 增加“今日焦点”入口，围绕今日任务、逾期任务、资料状态和最近问答给出下一步行动。
- Materials 默认使用资料卡片视图，保留表格管理模式。
- Chat 使用三栏工作台视觉结构：左侧历史，中间问答，右侧范围和证据；但本轮继续基于 `ChatHistory` 兼容实现。
- Plans 使用计划卡片和任务看板，明确今日、即将到期、未安排、已完成任务状态。
- 增加必要的轻量后端字段、查询参数和校验，支撑前端稳定展示。

### 暂不做

- 暂不做测验、错题本、闪卡、掌握度评分、间隔复习算法。
- 暂不做教师端、班级协作、多角色权限、公开分享、支付或通知系统。
- 暂不把 AI 生成内容自动写入数据库。
- 暂不把真实 `ChatConversation` / `ChatMessage` 持久化模型纳入最低可交付 redesign 验收；该能力列入 Phase 3 独立审批。
- 暂不承诺异步上传处理队列；当前上传请求仍同步处理。

---

## 1. 背景与当前问题

当前系统已具备资料上传、文件夹管理、资料详情、AI 问答、学习计划、今日任务、个人设置、统计仪表盘等核心能力。现有前端使用 Vue 3、Element Plus、ECharts、Pinia、Vue Router；后端使用 Flask、JWT、SQLAlchemy，并已支持资料切片、视觉资料索引、RAG 问答与基础统计。

主要问题是“功能存在，但学习闭环不够强”：

1. Dashboard 偏统计看板，不像今日学习入口，用户进入后仍需自行判断下一步。
2. Materials 偏管理表格，不够像知识资料库，资料状态、知识密度、视觉资产和可提问能力没有被显性表达。
3. Material Detail 信息完整但层级偏数据查看器，不够学习化。
4. Chat 已支持资料问答，但工作台结构、范围解释、证据对照和历史恢复不够清晰。
5. Plans 能管理计划和任务，但计划进度、任务看板、撤销完成、逾期和未安排任务表达不足。
6. 后端部分返回字段不足以支撑卡片化与驾驶舱展示，且日期参数校验容易出现 500。

---

## 2. 目标、非目标与交付边界

### 2.1 目标

1. 把 Dashboard 重塑为“今日学习驾驶舱”，用户进入后可直接看到今日焦点、节奏、知识库健康、计划进度和下一步行动。
2. 把 Materials 重塑为“知识资料库”，默认卡片展示，保留表格管理模式。
3. 把 Chat 重塑为“AI 学习会话工作台”，清楚展示问答范围、引用证据和旧历史问答。
4. 把 Plans 重塑为“学习计划与今日任务”，通过计划卡片、任务看板和完成/撤销动作形成执行闭环。
5. 保留温暖学习风格，同时提高课程展示效果、状态完整度和可解释性。
6. 控制本轮规模，形成可一次实施和验收的计划。

### 2.2 非目标

1. 不做完整学习平台化能力：测验、错题、闪卡、掌握度、复习算法均不在本轮。
2. 不做大规模后端重构，不替换技术栈。
3. 不强制引入全局新 store，除认证和跨页复用状态外，优先使用组件状态、路由 query 和 localStorage。
4. 不把 AI 草稿直接写入数据库。
5. 不在最低可交付范围内建设真实多轮 conversation 数据模型。

### 2.3 最低可交付 redesign

最低可交付 redesign 只包含以下内容：

- Phase 1 全部内容。
- Phase 2 中的轻量字段、查询参数、日期校验和前端 fallback。
- Chat 使用现有 `ChatHistory` 虚拟分组，不新增 conversation 表。
- Dashboard 增强优先通过现有接口和少量汇总字段实现。
- 构建、手工验证、接口 smoke 测试全部通过。

如果时间受限，完成 Phase 1 后只补齐 Phase 2 的兼容字段和错误校验即可停止；Phase 3、Phase 4、Phase 5 需要单独确认后再进入实施。

---

## 3. 产品定位与核心学习循环

### 3.1 一句话定位

Personal Study Hub 是一个以今日学习为入口的温暖 AI 学习工作台，帮助学生把课程资料、AI 问答和学习计划组织成可执行、可复盘的日常学习闭环。

### 3.2 目标用户

- 需要整理课程资料、实验文档、复习笔记的学生。
- 希望利用 AI 快速理解资料、追问概念、生成学习任务的学习者。
- 需要展示“资料处理、RAG 问答、计划管理、可视化统计”完整能力的课程项目团队。

### 3.3 学习循环

1. 收集资料：在知识库上传资料，选择文件夹，系统解析文本、抽取视觉资产、生成摘要与关键词。
2. 理解资料：进入资料详情查看摘要、关键词、视觉资产和切片，从推荐问题进入 Chat。
3. AI 提问与证据核对：在 Chat 中选择通用、全部、文件夹或单份资料范围，查看回答和引用证据。
4. 转化为任务：在 Plans 手动创建计划和任务；AI 生成计划草稿属于后续独立里程碑。
5. 执行今日任务：Dashboard 与 Plans 都突出今日、逾期和未安排任务。
6. 复盘与下一步：Dashboard 根据任务、资料和历史问答生成下一步行动。

---

## 4. 信息架构与路由 query 契约

### 4.1 顶层导航

| 路由 | 页面名称 | 主要职责 |
|---|---|---|
| `/dashboard` | 今日驾驶舱 | 今日焦点、学习节奏、知识库健康、计划进度、AI 连续性、下一步行动 |
| `/materials` | 知识库 | 资料卡片库、文件夹书架、搜索筛选、上传、表格模式、AI 提问入口 |
| `/materials/:id` | 资料详情 | 资料摘要、处理状态、视觉资产、文本切片、基于资料提问 |
| `/chat` | AI 学习会话 | 历史问答、问答区、范围选择、证据引用、通用问答和资料问答 |
| `/plans` | 学习计划 | 计划卡片、今日重点、任务看板、任务创建与完成 |
| `/plans/:id` | 学习计划详情态 | 打开 Plans 页面，并选中或展开指定计划 |
| `/profile` | 个人设置 | 个人信息、学习目标、本地偏好、数据与 AI 设置说明 |

### 4.2 路由 query 契约

| 路由 | Query | 行为 |
|---|---|---|
| `/chat?scope_type=general&prompt=...` | `scope_type=general`，可选 `prompt` | 进入通用问答；`prompt` 只自动填入输入框，不自动发送。 |
| `/chat?scope_type=all&prompt=...` | `scope_type=all` | 进入全部资料问答；仅检索当前用户 ready 资料。 |
| `/chat?scope_type=folder&folder_id=5&prompt=...` | `folder_id` 必填 | 文件夹存在且归属当前用户时选中文件夹；无效时回退 `all` 并显示错误横幅。 |
| `/chat?scope_type=material&material_id=123&prompt=...` | `material_id` 必填 | 资料存在、归属当前用户且 ready 时选中资料；无效或未 ready 时回退 `all` 并提示原因。 |
| `/plans?task_scope=today` | `task_scope=today|overdue|upcoming|unscheduled|completed` | 打开任务看板并应用对应筛选。 |
| `/plans/:id` | path param `id` | 选中或展开该计划，TaskBoard 默认按 `plan_id` 过滤；无效 id 显示错误横幅并清除选择。 |
| `/materials?folder_id=5&status=failed` | `folder_id`、`status` | 应用资料筛选；无效 folder 回退全部资料并提示。 |
| `/materials?upload=1` | `upload=1` | 打开上传弹窗。 |

所有 query 跳转只预填状态，不自动执行会写库或调用 AI 的动作；发送问题、创建任务、保存计划必须由用户确认。

---

## 5. 统一视觉、状态与文案规范

### 5.1 视觉风格

- 关键词：温暖、可信、清爽、学习手账、克制 AI 工作台、轻量数据可视化。
- 背景保留暖米色到浅蓝渐变，可延续 `#fff7e8`、`#f4fbff`。
- 主色使用学习蓝；完成和 ready 使用薄荷绿；提醒使用珊瑚或黄色；危险状态使用红色。
- 页面主内容桌面端左右间距 32px，移动端 16px。
- 卡片圆角 18px 至 24px，大面板 24px 至 28px。
- 图表必须有相邻文字摘要，不能只靠图形表达。

### 5.2 响应式断点

| 宽度 | 布局规则 |
|---|---|
| `>=1200px` | Dashboard 可 2-3 列；Chat 使用左中右三栏；Materials 文件夹书架 + 卡片网格。 |
| `768px-1199px` | 卡片两列；Chat 左侧历史可折叠，证据区改抽屉或下移；表格优先横向滚动或卡片替代。 |
| `<768px` | 单列布局；侧边栏改抽屉；Chat 使用消息流 + 底部范围/证据 sheet；文件夹书架改横向筛选。 |
| 最小支持宽度 | 360px；390px 移动端模拟需手工验证。 |

### 5.3 可访问性要求

- 保留 skip link。
- 卡片主行动必须是 `button` 或 `a/router-link`，不能只在 `div` 上绑定点击。
- Dialog 打开后 trap focus，关闭后恢复到触发按钮。
- 证据折叠面板使用 `aria-expanded`。
- 图表旁提供文字摘要。
- 状态不能只靠颜色表达，必须有文字徽标。
- `prefers-reduced-motion` 下禁用非必要动画。
- 键盘可完成：上传入口、资料详情、Chat 发送、任务完成/撤销、个人设置保存。

### 5.4 StatusBadge 映射表

| code | 中文标签 | tone | 行为说明 |
|---|---|---|---|
| `ready` | 已可提问 | success | 资料可进入 Chat。 |
| `processing` | 处理中 | warning | 资料问答按钮禁用，说明“处理完成后可提问”。 |
| `failed` | 处理失败 | danger | 显示失败原因、重建索引、删除重传。 |
| `todo` | 待完成 | neutral | 任务可点击完成。 |
| `done` | 已完成 | success | 任务可撤销完成。 |
| `overdue` | 已逾期 | danger | 未完成且 due_date 早于今天。 |
| `not_started` | 未开始 | neutral | 计划未来开始且未完成任何任务。 |
| `active` | 进行中 | primary | 计划正常推进。 |
| `empty` | 暂无任务 | neutral | 零任务计划的状态。 |
| `unknown` | 状态未知 | neutral | 缺失字段或未知 code 的兜底。 |

UI 展示“视觉资产”，统一指从上传资料中抽取的页面截图、图片、图表等可作为证据的视觉内容，不再混用“视觉资料数量”“视觉资料数”等术语。

---

## 6. 页面设计与优先级

优先级说明：P0 为最低可交付必须完成；P1 为本轮建议完成；P2 为后续展示打磨，不阻塞最低验收。

### 6.1 Dashboard：今日学习驾驶舱

页面目标：用户在 30 秒内知道今天先学什么、当前状态如何、下一步该做什么。

#### P0 必须实现

1. 统一 PageHeader：标题“今日驾驶舱”，副标题展示学习目标和日期。
2. 今日学习焦点卡：
   - 优先显示逾期未完成任务。
   - 其次显示今日未完成任务。
   - 再显示处理失败资料、未分类资料、新 ready 资料或最近问答。
3. 复用现有统计：资料数、AI 问答数、任务完成率、今日任务数。
4. 7 日学习节奏：复用 `/api/stats/task-trend`，提供文字摘要。
5. 空状态：无资料、无计划、无任务、无问答时给出具体按钮。

#### P1 建议实现

1. 知识库健康度：ready、processing、failed、uncategorized 数量。
2. 活跃计划摘要：计划数、平均进度、下一任务。
3. AI 连续性：最近历史问答和继续学习入口。
4. 推荐下一步行动：最多 5 条。

#### P2 后续打磨

- 更精细图表、趋势卡、推荐说明文案和课程演示数据。

#### today_focus 与 next_actions 排序规则

`today_focus` 和 `next_actions` 使用同一候选池，只是 `today_focus` 取最高优先级 1 条，`next_actions` 取前 5 条。

候选项 schema：

```json
{
  "type": "overdue_task",
  "title": "完成数据库实验报告",
  "reason": "已逾期 1 天",
  "priority": 100,
  "route": "/plans?task_scope=overdue",
  "action_label": "处理逾期任务"
}
```

优先级从高到低：

1. `overdue_task`：逾期未完成任务，priority 100。
2. `due_today`：今日未完成任务，priority 90。
3. `failed_material`：处理失败资料，priority 80。
4. `unclassified_material`：未分类资料，priority 70。
5. `recent_chat`：最近问答，priority 60。
6. `ready_new_material`：最近 ready 资料，priority 50。
7. `empty_start`：无数据引导，priority 40。

### 6.2 Materials：知识资料库

页面目标：把资料管理从表格列表升级为可浏览、可筛选、可提问的知识库，同时保留管理效率。

#### P0 必须实现

1. 默认卡片视图，表格视图可切换。
2. 顶部概览：全部资料、已可提问、处理中、处理失败、视觉资产总数。
3. 文件夹书架：全部资料、未分类、各文件夹；显示资料数、ready 数、processing 数、failed 数。
4. 资料卡：标题、类型、文件夹、状态、摘要、关键词、chunk 数、视觉资产数、创建时间或更新时间。
5. ready 资料显示“向这份资料提问”；非 ready 资料禁用并显示原因。
6. 上传弹窗保持同步处理体验：按钮显示“上传/解析中”，直到接口响应。

#### P1 建议实现

1. 前端筛选：关键词、文件类型、状态、文件夹、是否有视觉资产。
2. 前端排序：最近创建、标题、状态、资料丰富度。
3. 后端逐步支持同名查询参数，减少前端拉取压力。

#### 资料丰富度定义

`richness_score = chunk_count + visual_asset_count * 3 + min(keyword_count, 5)`。

Phase 1 前端基于列表字段计算；Phase 2 后端可直接返回或仍由前端计算。排序 `richness_desc` 按该分数降序，相同分数按 `created_at` 降序。

#### 上传规则

- 当前上传接口 `_process_material(material)` 同步执行，上传请求会阻塞到解析、摘要、切片、视觉资产索引尝试结束后再返回。
- Phase 1 UI 显示“上传/解析中”直到响应返回，不承诺后台队列和轮询。
- 只有未来引入异步任务队列后，列表中才可能长期看到 `processing` 持续状态。
- 支持格式以后端 `SUPPORTED_FILE_TYPES_LABEL` 和接口错误消息为准，前端不硬编码 PPTX/XLSX 等格式列表。

### 6.3 Material Detail：资料详情

页面目标：让用户理解单份资料的内容结构、处理质量和可提问范围，并能从详情页自然进入 AI 学习。

#### P0 必须实现

1. 顶部资料头：标题、文件名、文件夹、类型、状态、返回知识库、重建索引、基于资料提问。
2. 摘要与关键词：摘要只表达内容，不混入处理失败原因。
3. 推荐问题：前端用静态规则生成 3-5 个问题，例如“这份资料主要讲了什么？”“请总结关键词 X 的重点”。
4. 资料健康区：chunk 数、视觉资产数、ready/failed 视觉资产数、失败原因。
5. 视觉资产网格：缩略图、页码、caption、状态；图片失败时显示占位说明。
6. 文本切片默认折叠，支持搜索和复制。

#### P1 建议实现

- 点击视觉资产打开预览抽屉。
- 从切片发起问题时跳转 `/chat?scope_type=material&material_id=...&prompt=...`，只预填不自动发送。

### 6.4 Chat：AI 学习会话工作台

页面目标：既支持通用学习问答，也支持围绕资料、文件夹或全部资料的证据型问答；范围、证据和历史必须清楚。

#### P0 必须实现

1. 三栏视觉结构：
   - 左侧：历史问答列表，基于 `GET /api/chat/history`。
   - 中间：问答消息流和输入框。
   - 右侧：范围选择器和证据面板。
2. 继续使用 `ChatHistory`：每条历史记录展示为只读“历史问答”。
3. 通过前端虚拟会话分组展示当前页面内的连续上下文；刷新后以 `ChatHistory` 单条记录恢复，旧历史不能直接作为可多轮继续的 conversation。
4. `POST /api/chat` 增加 `scope_type` 请求字段，用于区分通用问答和全部资料问答。
5. AI 回答底部只保留复制、继续追问、重试；“生成任务 / 加入计划草稿”列入 Phase 4 可选。

#### 范围模式

| `scope_type` | 行为 |
|---|---|
| `general` | 不检索资料，直接调用 AI 通用问答；references 返回空数组。 |
| `all` | 从当前用户全部 `status=ready` 资料中 RAG 检索。 |
| `folder` | `folder_id` 必填且属于当前用户；仅检索该文件夹 ready 资料。 |
| `material` | `material_id` 必填且属于当前用户且 ready；仅检索该资料。 |

#### `POST /api/chat` 请求契约

请求：

```json
{
  "question": "请解释数据库索引的作用",
  "scope_type": "material",
  "material_id": 123,
  "folder_id": null,
  "conversation": [
    {"role": "user", "content": "上一轮问题"},
    {"role": "assistant", "content": "上一轮回答"}
  ]
}
```

兼容规则：

- 旧请求若省略 `scope_type`：维持当前行为。
- 当前行为定义为：如果有 `material_id`，按单份资料检索；如果有 `folder_id`，按文件夹检索；如果两者都为空，执行全部资料 RAG 检索。
- 新前端必须显式传 `scope_type`，避免 `general` 与 `all` 混淆。
- `general` 可调用 `AIService.chat` 或新增轻量包装；回答不保存资料引用。
- `all` 若没有 ready 资料，返回 400：`当前暂无可问答的资料，请先上传并处理资料，或切换为通用问答`。

#### references_json 统一 schema

每个引用项最多保留 `content_preview` 300 字，必须存 title 快照，删除资料后仍能展示历史来源名称。

```json
{
  "type": "text",
  "material_id": 123,
  "material_title": "数据库实验讲义",
  "folder_id": 5,
  "folder_name": "数据库课程",
  "chunk_id": 88,
  "chunk_index": 3,
  "asset_id": null,
  "page_number": null,
  "caption": null,
  "content_preview": "索引是一种帮助数据库快速定位记录的数据结构...",
  "score": 0.18
}
```

视觉引用 `type="visual"` 或兼容当前 `type="image"`，前端统一显示为“视觉证据”。

#### Chat 并发与失败规则

- 同一当前会话请求 pending 时禁用发送按钮。
- 本轮不提供取消按钮；不展示无法生效的 cancel。
- 请求失败时保留输入草稿和用户问题，显示错误气泡。
- “重试”使用同一 user message 重新发送；成功后替换失败的 assistant 气泡，不追加重复失败记录。
- Ctrl+Enter 发送；空问题显示输入区错误。

#### 视觉证据缩略图认证规则

- 不使用裸 `<img src="/api/materials/assets/:id/image">` 加载受 JWT 保护的图片。
- 使用 `materialApi.assetImage(assetId)` 通过带 Bearer header 的请求获取 blob，生成 ObjectURL 展示。
- 组件卸载或引用变化时 revoke ObjectURL。
- 404 或图片文件缺失时显示占位，不影响文本问答。

### 6.5 Plans：学习计划与今日任务

页面目标：把计划从普通列表升级为可执行的今日任务系统。

#### P0 必须实现

1. 顶部今日重点条：今日任务数、完成数、逾期数、最重要任务。
2. 计划卡片：标题、描述、日期范围、进度、任务数、下一任务、状态。
3. 任务看板四列：今日、即将到期、未安排、已完成。
4. TaskCard 动作：
   - `todo` 任务显示“完成”。
   - `done` 任务显示“撤销完成”。
   - 撤销调用 `POST /api/tasks/:id/undo`，设置 `status=todo`，清空 `completed_at`。
   - 操作成功后刷新计划进度、任务看板和 Dashboard stats。
5. `/plans/:id` 选中对应计划并过滤任务；无效 id 显示错误横幅。

#### P1 建议实现

1. 统一 `GET /api/tasks` 查询接口。
2. 计划计算字段后端返回。
3. 任务编辑表单校验和日期错误提示。

#### 任务看板分栏规则

| 分栏 | 进入条件 |
|---|---|
| 今日 | `status=todo` 且 `due_date=today`。 |
| 即将到期 | `status=todo` 且 `due_date>today`，按日期升序。 |
| 未安排 | `status=todo` 且 `due_date=null`。 |
| 已完成 | `status=done`，按 `completed_at` 降序。 |

逾期任务不单独占一列，显示在今日重点条和筛选中；在看板中可置顶于“今日”列上方或通过 `task_scope=overdue` 过滤展示，徽标为“已逾期”。

#### 计划状态与进度规则

计算优先级：

1. `task_count > 0 && done_count == task_count`：`status=completed`。
2. 存在 `status=todo` 且 `due_date < today`：`status=overdue`。
3. `task_count == 0`：`progress_percent=0`，`status=empty`。
4. `start_date` 存在且 `today < start_date` 且 `done_count == 0`：`status=not_started`。
5. 其他情况：`status=active`。

字段：

- `task_count`
- `done_count`
- `todo_count`
- `progress_percent`
- `next_due_task`
- `status`
- `overdue_count`

### 6.6 Profile：个人设置

页面目标：维护个人学习身份、学习目标和基础偏好，为后续 AI 个性化预留入口。

#### P0 必须实现

1. 个人学习身份卡：头像、昵称、用户名、学习目标。
2. 学习目标同步显示在 AppLayout 顶部栏和 Dashboard。
3. 本地偏好使用 localStorage，不阻塞后端：
   - `studyhub.defaultScope`：默认 `all`。
   - `studyhub.answerStyle`：默认 `step_by_step`。
   - `studyhub.evidenceExpanded`：默认 `false`。
   - `studyhub.defaultTaskMinutes`：默认 `30`。

#### P1 建议实现

- 展示“资料与 AI 偏好”“学习计划偏好”“数据与安全说明”。
- 如果后续需要跨设备同步，再新增后端 profile preference 字段。

---

## 7. 数据与 API 契约

### 7.1 Dashboard：`GET /api/stats/dashboard`

保留当前字段，并统一增强字段命名。

响应 schema：

```json
{
  "total_materials": 12,
  "total_chats": 28,
  "total_tasks": 20,
  "done_tasks": 8,
  "today_tasks": 3,
  "today_done_tasks": 1,
  "completion_rate": 40.0,
  "weak_points": [{"name": "索引", "count": 3}],
  "recent_chats": [],
  "today_focus": null,
  "knowledge_health": {
    "total": 12,
    "ready": 9,
    "processing": 1,
    "failed": 1,
    "uncategorized": 2,
    "visual_asset_count": 14
  },
  "active_plan_summary": {
    "active_count": 2,
    "average_progress_percent": 45,
    "next_due_task": null
  },
  "next_actions": [],
  "ai_continuity": {
    "recent_item": null,
    "route": "/chat"
  }
}
```

命名规则：

- 使用 `active_plan_summary`，不使用 `active_plans`。
- 保留 `recent_chats` 作为当前接口字段。
- `recent_conversations` 仅 Phase 3 启用；前端 fallback 为 `recent_conversations ?? recent_chats ?? []`。
- `weak_points` 当前实际来源是资料关键词和未完成任务标题词，因此 UI 文案改为“高频 / 待复习关键词”，不称为真实薄弱知识点。

缺字段 fallback：

- 数字字段默认 `0`。
- 数组默认 `[]`。
- 对象默认空结构。
- `today_focus` 缺失时，前端从 `/api/tasks/today`、`GET /api/tasks?scope=overdue`、`GET /api/materials`、`GET /api/chat/history` 组合生成。
- `knowledge_health` 缺失时，前端从 `/api/materials` 统计。
- `ai_continuity` 缺失时，前端使用 `recent_chats[0]`。

### 7.2 Materials：`GET /api/materials`

#### Phase 1

- 只保证现有 `folder_id` 后端筛选。
- 关键词、文件类型、状态、是否有视觉资产、排序由前端对已拉取列表进行 client-side filtering。

#### Phase 2

增加查询参数：

| 参数 | 说明 | 无效行为 |
|---|---|---|
| `q` | 标题、文件名、摘要、关键词模糊搜索 | 空字符串忽略。 |
| `file_type` | 文件类型，如 `pdf`、`txt` | 无匹配返回空数组。 |
| `status` | `ready|processing|failed` | 非法值返回 400。 |
| `folder_id` | 文件夹 id；空表示全部 | 不属于当前用户返回 404。 |
| `has_visual_assets` | `true|false` | 非法值返回 400。 |
| `sort` | `created_desc|title_asc|status|richness_desc` | 非法值回退 `created_desc` 并在响应 header 或 message 中提示。 |

列表项字段：

```json
{
  "id": 123,
  "user_id": 1,
  "folder_id": 5,
  "folder_name": "数据库课程",
  "title": "索引与事务",
  "file_name": "db-index.pdf",
  "file_type": "pdf",
  "summary": "...",
  "keywords": ["索引", "事务"],
  "status": "ready",
  "error_message": "",
  "created_at": "2026-06-08T12:00:00",
  "updated_at": "2026-06-08T12:01:00",
  "chunk_count": 18,
  "visual_asset_count": 6,
  "ready_visual_asset_count": 5,
  "failed_visual_asset_count": 1,
  "preview_asset_id": 99
}
```

### 7.3 Material folders：`GET /api/material-folders`

响应字段：

```json
{
  "id": 5,
  "user_id": 1,
  "name": "数据库课程",
  "description": "课程讲义与实验材料",
  "created_at": "2026-06-08T12:00:00",
  "material_count": 8,
  "ready_count": 6,
  "processing_count": 1,
  "failed_count": 1
}
```

所有 count 只统计当前 JWT 用户拥有的资料。删除文件夹仍沿用当前行为：资料移动到未分类，文件夹删除。

### 7.4 Tasks：`GET /api/tasks`

查询参数：

| 参数 | 说明 |
|---|---|
| `scope=today` | 今日未完成和已完成任务，`due_date=today`。 |
| `scope=overdue` | `status=todo` 且 `due_date<today`。 |
| `scope=upcoming` | `status=todo` 且 `due_date>today`。 |
| `scope=unscheduled` | `status=todo` 且 `due_date=null`。 |
| `plan_id` | 按计划筛选；必须属于当前用户。 |
| `status=todo|done` | 按状态筛选。 |
| `from=YYYY-MM-DD` | 起始日期，含当天。 |
| `to=YYYY-MM-DD` | 结束日期，含当天。 |

返回字段在 `StudyTask.to_dict()` 基础上增加：

```json
{
  "plan_title": "数据库期末复习",
  "is_overdue": true,
  "days_until_due": -1
}
```

校验：

- 无效日期格式返回 400：`日期格式必须为 YYYY-MM-DD`。
- `to` 早于 `from` 返回 400：`结束日期不能早于开始日期`。
- 非法 `status` 或 `scope` 返回 400。
- `plan_id` 不属于当前用户返回 404，避免泄露跨用户数据。
- `GET /api/tasks/today` 保留兼容。

### 7.5 Plans：`GET /api/plans`

保留 `include_tasks=True` 行为，同时增加计划计算字段。日期校验同 tasks：

- `start_date`、`end_date` 格式必须为 `YYYY-MM-DD`。
- `end_date < start_date` 返回 400。
- 任务 `due_date` 是否允许超出计划范围：本轮允许保存，但前端显示 warning：“该任务日期不在计划周期内”。不阻塞创建。

### 7.6 Chat：接口补充

`chatApi.ask(data)` 继续调用 `POST /api/chat`。前端 API 模块补充但不强制立即使用 Phase 3 方法：

```js
export const chatApi = {
  ask: (data) => http.post('/chat', data),
  history: () => http.get('/chat/history'),
  conversations: (params = {}) => http.get('/chat/conversations', { params }),
  createConversation: (data) => http.post('/chat/conversations', data),
  messages: (id) => http.get(`/chat/conversations/${id}/messages`),
  sendMessage: (id, data) => http.post(`/chat/conversations/${id}/messages`, data)
}
```

Phase 1/2 中 `conversations`、`createConversation`、`messages`、`sendMessage` 不被主流程依赖；如果后端未实现，前端不调用。

### 7.7 AI plan preview：Phase 4 独立契约

AI 计划草稿不纳入最低 redesign。若进入 Phase 4，字段统一为：

请求：

```json
{
  "goal": "两周内复习数据库索引和事务",
  "start_date": "2026-06-09",
  "end_date": "2026-06-23",
  "available_minutes_per_day": 45,
  "study_days_per_week": 5,
  "material_ids": [1, 2],
  "folder_id": null,
  "style": "exam_review"
}
```

校验：

- `available_minutes_per_day`：10-480。
- `study_days_per_week`：1-7。
- 日期格式和范围同 Plans。
- `material_ids`、`folder_id` 必须属于当前用户。

保存流优先使用事务接口 `POST /api/plans/from-preview`。如果不实现事务接口，则前端补偿规则为：先创建 plan，再顺序创建 tasks；任一任务失败时显示“部分保存成功”警告，提供重试未保存任务和删除刚创建计划两个动作。

前端 API 模块补充：

```js
planApi.aiPreview = (data) => http.post('/plans/ai-preview', data)
planApi.createFromPreview = (data) => http.post('/plans/from-preview', data)
taskApi.list = (params = {}) => http.get('/tasks', { params })
```

---

## 8. 数据库变更与迁移策略

当前项目未发现迁移目录；本轮数据库变更采用“启动前手工/脚本式 schema 更新 + 兼容默认值”的方式，具体执行方式由实现计划在后端初始化流程中确认，但不得留下占位。

### 8.1 最低可交付需要新增的列

`material` 表：

- `updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)`
- `error_message = db.Column(db.Text, default="")`

API 行为：

- `status=failed` 时 `error_message` 返回失败原因。
- `summary` 只保存内容摘要，不再承载失败原因。
- 老数据若没有 `updated_at`，返回时 fallback 为 `created_at`。
- 老数据若没有 `error_message`，返回空字符串；如历史失败原因写在 `summary`，前端可只在兼容提示中展示 summary，但新处理失败必须写 `error_message`。

### 8.2 最低可交付不新增的表

本轮不新增：

- `chat_conversation`
- `chat_message`
- profile preference 后端字段

这些仅在 Phase 3 或后续单独里程碑启用。

### 8.3 Phase 3 可选数据库变更

如后续批准持久化 conversation，再新增：

`chat_conversation`：

- `id`
- `user_id`
- `title`
- `scope_type`: `general|all|folder|material`
- `folder_id`
- `material_id`
- `last_message_at`
- `message_count`
- `created_at`
- `updated_at`

`chat_message`：

- `id`
- `conversation_id`
- `user_id`
- `role`: `user|assistant|system`
- `content`
- `references_json`
- `status`: `success|failed`
- `error_message`
- `model_name`
- `created_at`

兼容规则：Phase 3 前左侧列表显示 `ChatHistory` 为只读“历史问答”；Phase 3 后可选择一条历史记录回填为一个 conversation，或保留单独“旧问答记录”区。旧历史默认不能多轮继续，除非用户点击“转换为会话”。

---

## 9. 安全、权限与数据完整性

1. 所有新增接口必须使用 JWT。
2. 所有查询必须按 `current user_id` 过滤。
3. 访问跨用户资料、文件夹、计划、任务、conversation、message 时返回 404，不返回 403，避免暴露资源存在性。
4. Chat 的 `material_id`、`folder_id` 必须校验归属当前用户。
5. 资料删除后的历史引用：
   - `references_json` 必须保存 `material_title` 和 `folder_name` 快照。
   - 若资料已删除，历史引用保留文本和标题，跳转链接禁用并显示“资料已删除”。
   - 不级联删除历史问答。
6. 视觉资产图片仍通过 JWT 保护接口读取，前端用 blob 获取。
7. AI 与数据说明在 Profile 展示：资料仅用于当前用户知识库检索和个人学习问答。

---

## 10. 状态、错误与 fallback

### 10.1 全局状态

| 状态 | 表现 | 用户行动 |
|---|---|---|
| loading | 骨架屏、按钮 loading、明确文字 | 等待 |
| empty | 解释原因、主行动按钮 | 上传资料、创建计划、开始问答 |
| success | 成功提示、数据刷新 | 继续下一步 |
| warning | 黄色提示条、处理中或需选择范围 | 选择范围、稍后刷新 |
| error | 错误横幅、错误消息、重试按钮 | 重试、重建索引、调整输入 |
| disabled | 禁用按钮加原因 | 完成前置条件 |

### 10.2 空状态动作表

| 场景 | 文案 | 主行动 |
|---|---|---|
| 无资料 | “上传第一份课程资料，让 AI 帮你整理重点。” | 跳转 `/materials?upload=1` 并打开上传弹窗。 |
| 无计划 | “创建一个本周学习计划，把目标拆成任务。” | `/plans` 打开创建计划弹窗。 |
| 无会话 | “向知识库提出第一个问题。” | `/chat?scope_type=all`，无资料时建议切换通用问答。 |
| 无今日任务 | “今天还没有安排任务，可以添加一个 15 分钟轻量任务。” | `/plans?task_scope=today` 并打开快速任务弹窗，`due_date=today`。 |
| 无待复习关键词 | “继续上传资料或完成任务后会生成关键词提示。” | `/materials`。 |

### 10.3 字段 fallback 表

| 字段 | 缺失时默认值 |
|---|---|
| count 类字段 | `0` |
| 数组字段 | `[]` |
| 状态字段 | `unknown` |
| `progress_percent` | `0` |
| `updated_at` | `created_at` |
| `error_message` | `""` |
| `today_focus` | 前端按排序规则生成 |
| `knowledge_health` | 前端从资料列表统计 |
| `recent_conversations` | `recent_chats` |
| `ai_continuity` | 最近一条 `recent_chats` 或空状态 |

---

## 11. 组件范围控制

### 11.1 最低可交付必需复用组件

- `PageHeader`
- `WorkbenchPanel`
- `MetricCard`
- `StatusBadge`
- `EmptyGuide`
- `MaterialCard`
- `PlanCard`
- `TaskCard`
- `MessageBubble`

### 11.2 页面局部组件，可按需拆分

- `FolderShelf`
- `MaterialFilters`
- `UploadMaterialDialog`
- `VisualAssetGrid`
- `ScopeSelector`
- `EvidencePanel`
- `TaskBoard`

### 11.3 延后组件

以下不纳入最低可交付，除非实现中已证明复用价值：

- `ContentGrid`
- `ProgressRing`
- `TrendChartCard` 的高级封装
- `KnowledgeHealthCard`
- `WeakPointTags`
- `ConversationList` 真实会话版
- `ThinkingIndicator` 独立组件
- `AiPlanPreviewDialog`

组件拆分以减少重复和提高可维护性为准，不为了命名而拆分。

---

## 12. 前端状态所有权

- Auth/profile：继续使用现有 auth store。
- AppLayout 顶部学习目标：从 auth store 当前用户读取。
- Materials 筛选和视图模式：
  - URL query 保存可分享筛选：`folder_id`、`status`、`q`。
  - localStorage 保存个人视图偏好：`studyhub.materialViewMode`。
- Chat 当前 scope、当前页面内虚拟消息：Chat 组件局部状态；如 Phase 3 conversation 启动，再考虑 chat store。
- Plans 筛选：URL query 保存 `task_scope`、`plan_id`。
- Profile 偏好：Phase 1 使用 localStorage。
- Dashboard 派生数据：组件局部 computed，避免新增全局 store。

---

## 13. 分阶段实施计划

### Phase 1：最低可交付视觉与交互重做

目标：不破坏后端主流程的前提下，完成核心页面工作台体验。

范围：

1. AppLayout：导航命名、顶部学习目标、暖色工作台层级。
2. 基础组件：`PageHeader`、`WorkbenchPanel`、`MetricCard`、`StatusBadge`、`EmptyGuide`。
3. Dashboard：今日焦点、现有 stats、7 日趋势、空状态、推荐行动 client-side 生成。
4. Materials：默认卡片模式、表格模式保留、文件夹书架、client-side 筛选和排序、同步上传状态。
5. MaterialDetail：摘要、关键词、健康区、视觉资产网格、切片折叠、基于资料提问跳转。
6. Chat：三栏布局、显式 `scope_type`、旧 `ChatHistory` 历史问答、证据面板、pending/失败/重试规则。
7. Plans：计划卡、四列任务看板、完成与撤销、`/plans/:id` 选中态。
8. Profile：学习目标联动、本地偏好。

验收：旧功能可用，主要页面视觉统一，`npm run build` 通过，手工主流程通过。

### Phase 2：轻量后端字段、筛选与校验

目标：补齐 Phase 1 展示所需字段和接口稳定性。

范围：

1. `Material.updated_at`、`Material.error_message`。
2. `Material.to_dict()` 增加 `chunk_count`、`visual_asset_count`、`ready_visual_asset_count`、`failed_visual_asset_count`、`preview_asset_id`。
3. `GET /api/material-folders` 增加 ready、processing、failed counts。
4. `GET /api/materials` 增加 Phase 2 查询参数。
5. `GET /api/tasks` 增加统一筛选。
6. Plans 和 Tasks 日期校验返回 400。
7. `GET /api/plans` 增加计算字段。
8. `GET /api/stats/dashboard` 增加统一增强字段，或确保前端 fallback 能稳定工作。

验收：API smoke tests 通过，新字段缺失 fallback 不报错，跨用户 id 返回 404。

### Phase 3：真实 Chat conversation 独立里程碑

目标：将 Chat 从旧单轮历史升级为持久化多轮会话。

范围：

- 新增 `chat_conversation`、`chat_message`。
- 新增 conversation API。
- 旧 `ChatHistory` 兼容展示和可选转换。
- 消息分页：默认加载最近 30 条，向上加载更多。

验收：多轮会话可恢复，旧历史不丢失，引用证据可回看。

### Phase 4：AI 计划草稿独立里程碑

目标：AI 只生成可编辑草稿，保存需用户确认。

范围：

- `POST /api/plans/ai-preview`。
- 可选事务保存 `POST /api/plans/from-preview`。
- 任务编辑预览和错误补偿。

验收：preview 不写库；保存成功后 plan/tasks 一致；失败有补偿路径。

### Phase 5：Dashboard 推荐与课程展示打磨

目标：形成完整演示闭环。

范围：

- 更完整的 `today_focus`、`next_actions`、`ai_continuity`。
- 演示数据准备。
- 图表、文案和响应式细节打磨。

验收：可从 Dashboard 演示上传资料、AI 问答、创建任务、完成任务、复盘进度。

---

## 14. 性能与非功能约束

- Dashboard Phase 1 首屏数据请求不超过 4 个：dashboard stats、task trend、tasks 或 plans、materials；如果 dashboard 增强字段完整，应减少到 2 个以内。
- Materials 超过 100 条资料时启用分页或虚拟滚动；Phase 1 可先分页。
- 视觉资产缩略图 lazy-load，只加载进入视口的图片。
- Chat 消息 Phase 1 只渲染当前虚拟会话和最近历史摘要；Phase 3 起默认加载最近 30 条消息，旧消息分页。
- 不默认渲染所有 chunks；MaterialDetail 切片区默认折叠并分页或按需展开。
- 避免在 Dashboard 直接渲染大体量资料列表。

---

## 15. 测试与验证

### 15.1 构建命令

在以下目录执行：

`D:\学习资料\大数据综合实践\zonghexitong\frontend`

命令：

```powershell
npm install
npm run build
```

若依赖已安装，可只执行 `npm run build`。

### 15.2 API smoke tests

所有接口均需带 JWT。

Tasks：

- `GET /api/tasks?scope=today` 只包含 `due_date=today` 的任务。
- `GET /api/tasks?scope=overdue` 只包含未完成且已逾期任务，不包含 done。
- `GET /api/tasks?from=2026-06-01&to=2026-06-08` 日期范围含首尾两天。
- `GET /api/tasks?status=todo&plan_id=...` 同时应用 status 和 plan_id。
- 无效日期返回 400。
- 未登录返回 401。
- 跨用户 plan_id 返回 404。

Plans：

- 零任务计划：`progress_percent=0`，`status=empty`。
- 全部任务 done：`status=completed`。
- 存在逾期 todo：`status=overdue`。
- 未来 start_date 且无完成任务：`status=not_started`。
- start_date 或 end_date 为 null 时不抛错；按状态优先级计算。
- end_date 早于 start_date 返回 400。

Materials：

- `GET /api/materials?status=ready` 只返回 ready。
- `has_visual_assets=true` 只返回视觉资产数大于 0 的资料。
- 非法 status 返回 400。
- 文件夹 counts 只统计当前用户。
- failed 资料返回 `error_message`。

Chat：

- `scope_type=general` 不返回引用。
- `scope_type=all` 在有 ready 资料时返回 RAG 结果。
- `scope_type=material` 对未 ready 资料返回 400。
- 跨用户 material_id 或 folder_id 返回 404。
- 省略 `scope_type` 仍兼容旧行为。

### 15.3 手工端到端流程

1. 注册或登录。
2. 进入 Dashboard，查看今日焦点和空状态。
3. 进入 Materials，上传资料，等待同步处理响应。
4. 查看资料卡片和详情页，验证视觉资产 blob 图片加载。
5. 从资料详情跳转 Chat，确认 scope 和 prompt 预填，不自动发送。
6. 发送资料问答，查看证据；发送通用问答，确认无资料检索标识。
7. 创建计划和任务，在 Plans 完成任务，再撤销完成。
8. 返回 Dashboard，确认任务和完成率更新。
9. 修改 Profile 学习目标，确认顶部栏和 Dashboard 显示更新。

### 15.4 浏览器与响应式矩阵

- Chrome desktop 1440px。
- Edge desktop 1440px。
- Desktop/tablet 1024px。
- Mobile emulation 390px。

页面覆盖：Dashboard、Materials、MaterialDetail、Chat、Plans、Profile。

### 15.5 可访问性检查

- 键盘-only 完成主要流程。
- Dialog focus trap 和 restore 正常。
- Evidence accordion 有 `aria-expanded`。
- 图表旁有文字摘要。
- reduced motion 下无非必要动画。
- 状态徽标都有文字。

---

## 16. 设计验收标准

1. `/dashboard` 首屏在 1366x768 下能看到今日焦点、核心指标和至少一个下一步行动。
2. 每个受保护主页面都有统一 PageHeader，且每页只有一个明确主 CTA。
3. `/materials` 默认进入卡片式知识库，可切换表格模式并保留原有管理能力。
4. 资料卡和资料详情能一键进入基于该资料的 Chat，未 ready 时说明原因。
5. `/chat` 能清楚显示当前 `scope_type`，并区分通用问答与资料问答。
6. Chat 回答能展示引用证据；无引用时显示“本次未找到资料证据”。
7. `/plans` 有今日、即将到期、未安排、已完成四类任务视图，支持完成和撤销。
8. `/profile` 中学习目标能影响 AppLayout 顶部栏和 Dashboard。
9. 所有核心页面都有 loading、empty、error、disabled 状态。
10. 新增字段缺失时前端 fallback 生效，不破坏当前已有数据。
11. 所有新增和增强接口按当前用户过滤，跨用户 id 返回 404。
12. 前端构建通过，手工主流程通过。
13. 视觉保持暖色学习风格，同时具备可观察标准：卡片间距一致、共享状态徽标、图表有文字摘要、主页面不再只有原始表格。