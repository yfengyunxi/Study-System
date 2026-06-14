# Study-System · 学习助手

个人学习助手系统。采用 Vue 3 + Flask + MySQL + Chroma 架构，支持学习资料管理、RAG 知识库问答、学习计划与任务、番茄钟专注计时和学习数据统计。

## 功能

### 用户
- 注册、登录、JWT 鉴权（7 天有效期）
- 个人学习目标设置
- 头像本地上传

### 知识库
- 自定义资料文件夹
- 上传 PDF、Word(doc/docx)、TXT、Markdown、PPTX、XLSX
- 自动解析文本、生成摘要、提取关键词、切片入库
- 双路多模态 RAG：文本检索 + PDF/PPT 图片检索
- 资料移动、删除、重建索引
- 索引状态追踪与轮询

### AI 对话
- 基于 Chroma 的 RAG 检索问答，返回答案和引用片段
- 多轮对话（Conversation），支持上下文延续
- 消息重试、会话管理
- 指定范围问答（全部资料 / 指定资料 / 指定文件夹）
- 旧版单轮问答兼容

### 学习计划
- 创建学习计划（含起止日期）
- 添加学习任务（支持截止日期、所属计划）
- 今日待办面板（按计划分组）
- 计划详情双列视图（待完成 / 已完成）
- 一键完成、任务编辑、已完成计划归档
- 逾期任务标记

### 专注计时
- 番茄钟计时器（可自定义 1-180 分钟）
- 时间戳计时，浏览器后台 / 切换页面不中断
- 右上角实时倒计时徽章
- 完成后自动记录专注时间

### 仪表盘
- 问候语 + 待办任务提示
- 核心指标卡片（资料数、问答数、完成率、今日专注）
- 任务完成趋势图（7 天折线图）
- 今日学习焦点（智能推荐下一步行动）
- 番茄钟 + 专注时长趋势图
- 知识库健康状态、资料类型分布饼图、最近问答

## 技术栈

**前端：**

- Vue 3（Composition API）
- Vite
- Vue Router
- Pinia
- Axios
- Element Plus
- ECharts

**后端：**

- Flask
- Flask-SQLAlchemy
- Flask-JWT-Extended
- PyMySQL
- ChromaDB
- pypdf
- python-docx
- openpyxl
- pywin32（Windows 下解析旧版 .doc）
- PyMuPDF
- markdown-it（前端渲染）

## 目录结构

```text
backend/
  app.py              # 应用入口
  config.py           # 配置（JWT、数据库、文件上传等）
  extensions.py       # Flask 扩展初始化
  models/             # 数据模型
    user.py
    material.py       # Material、Folder、Chunk、VisualAsset、ReindexJob
    plan.py           # StudyPlan、StudyTask
    chat.py           # ChatHistory、Conversation、Message、Citation
    focus.py          # FocusSession
  routes/             # API 路由
    auth.py           # 认证
    materials.py      # 资料 CRUD、上传、移动、重建索引
    folders.py        # 文件夹 CRUD
    chat.py           # AI 对话、会话管理
    plans.py          # 学习计划
    tasks.py          # 学习任务
    focus.py          # 专注记录
    stats.py          # 仪表盘统计
  services/           # 业务逻辑
    ai_service.py
    rag_service.py
    vector_store_service.py
    stats_service.py
    scope_service.py
    schema_service.py
    error_service.py
    chat_history_adapter.py
  uploads/            # 上传文件存储
  chroma_store/       # ChromaDB 向量库
  tests/              # API 测试

frontend/
  src/
    api/              # Axios 封装
    components/       # 通用组件
      AppLayout.vue   # 全局布局（侧边栏 + 顶栏 + 番茄钟徽章）
      study/          # 业务组件
    router/
    stores/           # Pinia 状态管理
      auth.js
      pomodoro.js     # 番茄钟跨页面状态
    utils/
      renderMarkdown.js
    views/            # 页面
      Dashboard.vue   # 仪表盘
      Plans.vue       # 学习计划
      Materials.vue   # 知识库
      Chat.vue        # AI 对话
      Profile.vue     # 个人设置
```

## 后端启动

本项目按 conda base 环境运行：

```powershell
cd backend
conda activate base
python -m pip install -r requirements.txt
copy .env.example .env
```

创建 MySQL 数据库：

```sql
CREATE DATABASE study_system DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

按实际账号修改 `backend/.env`：

```text
DATABASE_URL=mysql+pymysql://root:123456@localhost:3306/study_system?charset=utf8mb4
```

启动后端：

```powershell
python app.py
```

默认地址：`http://localhost:5000`

### 创建测试数据

```powershell
# 基础种子数据（5 个计划 + 任务）
python seed_plans.py

# 扩充数据（额外计划、任务、专注记录）
python enrich_test_data.py
```

两个脚本均为幂等，可重复运行。测试账号：`test` / `123456`

## AI 配置

系统支持 OpenAI 兼容接口。在 `backend/.env` 中配置：

```text
# 问答模型
CHAT_BASE_URL=https://api.xiaomimimo.com/v1
CHAT_API_KEY=你的 API Key
CHAT_MODEL=mimo-v2.5
CHAT_WIRE_API=chat_completions

# 多模态 RAG（可选）
MULTIMODAL_RAG_ENABLED=true
MULTIMODAL_EMBEDDING_API_KEY=你的 DashScope API Key
MULTIMODAL_EMBEDDING_MODEL=qwen3-vl-embedding
EMBEDDING_MODEL=qwen3-vl-embedding
MULTIMODAL_TOP_K=3
```

配置后，系统会为 PDF 页面图和 PPTX 内嵌图片建立视觉向量索引。未配置时，文本 RAG 仍可正常使用。

如果不配置 AI API，系统降级运行：
- 摘要使用文本截取
- 关键词使用词频统计
- embedding 使用本地哈希向量
- 问答返回检索片段整理结果

## 前端启动

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

默认地址：`http://localhost:5173`

## 演示流程

1. 注册并登录（或使用测试账号 `test` / `123456`）
2. 在"知识库"上传 PDF、Word、TXT、Markdown、PPTX 或 XLSX
3. 查看资料摘要、关键词和文本切片
4. 进入"AI 学习会话"，选择范围提问
5. 创建学习计划和学习任务
6. 在"今日待办"标记任务完成
7. 使用番茄钟记录专注时间
8. 回到仪表盘查看统计图表和学习焦点建议

## API 概览

### 认证

```text
POST   /api/auth/register         注册
POST   /api/auth/login            登录
GET    /api/auth/me               当前用户信息
PUT    /api/auth/profile          更新个人资料
POST   /api/auth/avatar           上传头像
GET    /api/auth/avatar/<user_id> 获取头像图片
```

### 资料文件夹

```text
GET    /api/material-folders       列表
POST   /api/material-folders       创建
PUT    /api/material-folders/<id>  更新
DELETE /api/material-folders/<id>  删除
```

### 学习资料

```text
GET    /api/materials                        列表（支持 folder_id 筛选）
POST   /api/materials/upload                 上传
GET    /api/materials/<id>                   详情
PUT    /api/materials/<id>/move              移动到文件夹
DELETE /api/materials/<id>                   删除
POST   /api/materials/<id>/reindex           重建索引
GET    /api/materials/<id>/index-status      索引状态
GET    /api/materials/<id>/assets            视觉资产列表
GET    /api/materials/assets/<asset_id>/image 视觉资产图片
```

### AI 对话

```text
# 新版多轮对话
GET    /api/chat/conversations                    会话列表
POST   /api/chat/conversations                    创建会话
DELETE /api/chat/conversations/<id>               删除会话
GET    /api/chat/conversations/<id>/messages      消息列表
POST   /api/chat/conversations/<id>/messages      发送消息
POST   /api/chat/messages/<id>/retry              重试消息

# 旧版单轮问答（兼容）
POST   /api/chat                                  提问
GET    /api/chat/history                          历史列表
GET    /api/chat/history/<id>                     历史详情

# AI 状态
GET    /api/chat/ai-status                        检查 AI 配置
```

### 学习计划

```text
GET    /api/plans       列表
POST   /api/plans       创建
GET    /api/plans/<id>  详情
PUT    /api/plans/<id>  更新
DELETE /api/plans/<id>  删除
```

### 学习任务

```text
GET    /api/tasks              列表（支持 plan_id 筛选）
GET    /api/tasks/today        今日任务
POST   /api/tasks              创建
PUT    /api/tasks/<id>         更新
DELETE /api/tasks/<id>         删除
POST   /api/tasks/<id>/complete 标记完成
POST   /api/tasks/<id>/undo    撤销完成
```

### 专注记录

```text
POST   /api/focus/sessions     创建专注记录
```

### 统计

```text
GET    /api/stats/dashboard     仪表盘综合统计
GET    /api/stats/task-trend    任务完成趋势
GET    /api/stats/focus-trend   专注时长趋势
GET    /api/stats/material-types 资料类型分布
GET    /api/stats/folders       文件夹资料统计
```
