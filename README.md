# Study-System

个人学习助手系统，课程项目级实现。系统采用 Vue 3 + Flask + MySQL + Chroma 架构，支持学习资料管理、RAG 知识库问答、学习计划任务和学习数据统计。

## 功能

- 用户注册、登录、JWT 鉴权、个人学习目标设置
- 自定义资料文件夹，按课程或知识类别管理资料
- 上传 PDF、Word(doc/docx)、TXT、Markdown、PPTX、XLSX 学习资料
- 自动解析资料文本、生成摘要、提取关键词、切片入库
- 双路多模态 RAG：文本检索 + PDF/PPT 图片检索
- 基于 Chroma 的 RAG 检索问答，返回答案和引用片段
- 创建学习计划和任务，支持今日任务和完成/撤销
- 首页统计资料数、问答数、任务完成率、趋势图和资料类型占比

## 技术栈

前端：

- Vue 3
- Vite
- Vue Router
- Pinia
- Axios
- Element Plus
- ECharts

后端：

- Flask
- Flask-SQLAlchemy
- Flask-JWT-Extended
- PyMySQL
- ChromaDB
- pypdf
- python-docx
- openpyxl
- pywin32（Windows 下用于解析旧版 .doc）
- PyMuPDF

## 目录结构

```text
backend/
  app.py
  config.py
  models/
  routes/
  services/
  uploads/
  chroma_store/

frontend/
  src/
    api/
    components/
    router/
    stores/
    views/
```

## 后端启动

本项目按 conda base 环境运行。进入后端目录：

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

默认地址：

```text
http://localhost:5000
```

## AI 配置

系统支持 OpenAI 兼容接口。问答模型使用小米官方 OpenAI 格式，在 `backend/.env` 中配置：

```text
CHAT_BASE_URL=https://api.xiaomimimo.com/v1
CHAT_API_KEY=你的小米 API Key
CHAT_MODEL=mimo-v2.5
CHAT_WIRE_API=chat_completions
```

双路多模态 RAG 使用 DashScope `qwen3-vl-embedding` 作为视觉向量模型。在 `backend/.env` 中配置：

```text
MULTIMODAL_RAG_ENABLED=true
MULTIMODAL_EMBEDDING_API_KEY=你的 DashScope API Key
MULTIMODAL_EMBEDDING_MODEL=qwen3-vl-embedding
EMBEDDING_MODEL=qwen3-vl-embedding
MULTIMODAL_TOP_K=3
```

配置后，系统会为 PDF 页面图和 PPTX 内嵌图片建立视觉向量索引。未配置时，文本 RAG 仍可正常使用。

如果不配置 AI API，系统仍可运行演示版降级逻辑：

- 摘要使用文本截取
- 关键词使用词频统计
- embedding 使用本地哈希向量
- 问答返回检索片段整理结果

## 前端启动

进入前端目录：

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

默认地址：

```text
http://localhost:5173
```

## 演示流程

1. 注册并登录用户。
2. 在“学习资料”上传 PDF、Word(doc/docx)、TXT、Markdown、PPTX 或 XLSX。
3. 查看资料摘要、关键词和文本切片。
4. 进入“AI 问答”，选择全部资料或指定资料提问。
5. 创建学习计划和学习任务。
6. 标记今日任务完成。
7. 回到首页查看统计图表和最近问答。

## API 概览

认证：

```text
POST /api/auth/register
POST /api/auth/login
GET  /api/auth/me
PUT  /api/auth/profile
```

资料：

```text
POST   /api/material-folders
GET    /api/material-folders
PUT    /api/material-folders/<id>
DELETE /api/material-folders/<id>

POST   /api/materials/upload
GET    /api/materials
GET    /api/materials?folder_id=<id>
GET    /api/materials/<id>
DELETE /api/materials/<id>
POST   /api/materials/<id>/reindex
```

问答：

```text
POST /api/chat
GET  /api/chat/history
GET  /api/chat/history/<id>
```

计划和任务：

```text
POST   /api/plans
GET    /api/plans
GET    /api/plans/<id>
PUT    /api/plans/<id>
DELETE /api/plans/<id>

POST   /api/tasks
GET    /api/tasks/today
PUT    /api/tasks/<id>
DELETE /api/tasks/<id>
POST   /api/tasks/<id>/complete
POST   /api/tasks/<id>/undo
```

统计：

```text
GET /api/stats/dashboard
GET /api/stats/task-trend
GET /api/stats/material-types
GET /api/stats/folders
```
