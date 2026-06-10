import os
import tempfile
from datetime import date, datetime, timedelta

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("AUTO_CREATE_TABLES", "true")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret")
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("UPLOAD_FOLDER", tempfile.mkdtemp(prefix="studyhub-test-uploads-"))
os.environ.setdefault("CHROMA_DIR", tempfile.mkdtemp(prefix="studyhub-test-chroma-"))
os.environ.setdefault("AI_API_KEY", "")
os.environ.setdefault("CHAT_API_KEY", "")
os.environ.setdefault("TEXT_EMBEDDING_API_KEY", "")
os.environ.setdefault("MULTIMODAL_EMBEDDING_API_KEY", "")
os.environ.setdefault("MULTIMODAL_RAG_ENABLED", "false")

import pytest
from flask_jwt_extended import create_access_token

from app import create_app
from extensions import db
from models.chat import ChatHistory, Citation, Conversation, Message
from models.focus import FocusSession
from models.material import Material, MaterialChunk, MaterialFolder, MaterialVisualAsset
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
            index_state="ready" if status == "ready" else "not_indexed",
            sync_state="synced",
            active_index_generation=1 if status == "ready" else 0,
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


@pytest.fixture()
def make_conversation(app):
    def _make(user, title="新会话", status="active"):
        conversation = Conversation(user_id=user.id, title=title, status=status)
        db.session.add(conversation)
        db.session.commit()
        return conversation

    return _make


@pytest.fixture()
def make_message(app):
    def _make(conversation, role="user", content="问题", status="succeeded", request_id=None, **kwargs):
        message = Message(
            conversation_id=conversation.id,
            user_id=conversation.user_id,
            role=role,
            content=content,
            status=status,
            request_id=request_id,
            scope_snapshot_json=kwargs.get("scope_snapshot_json", '{"scope_type":"all"}'),
            parent_message_id=kwargs.get("parent_message_id"),
            retry_of_message_id=kwargs.get("retry_of_message_id"),
            error_code=kwargs.get("error_code"),
            retryable=kwargs.get("retryable", status in {"failed_timeout", "failed_error"}),
        )
        db.session.add(message)
        db.session.commit()
        return message

    return _make


@pytest.fixture()
def make_citation(app):
    def _make(message, material=None, preview="引用片段"):
        citation = Citation(
            message_id=message.id,
            type="text",
            material_id=material.id if material else None,
            material_title_snapshot=material.title if material else "",
            folder_id_snapshot=material.folder_id if material else None,
            folder_name_snapshot=material.folder.name if material and material.folder else "",
            preview=preview,
            source_state="active",
            generation=1,
        )
        db.session.add(citation)
        db.session.commit()
        return citation

    return _make


@pytest.fixture()
def make_focus_session(app):
    def _make(user, study_date=date.today(), duration_seconds=1500, client_session_id="pomo-test"):
        session = FocusSession(
            user_id=user.id,
            client_session_id=client_session_id,
            started_at=datetime.combine(study_date, datetime.min.time()),
            ended_at=datetime.combine(study_date, datetime.min.time()) + timedelta(seconds=duration_seconds),
            duration_seconds=duration_seconds,
            planned_seconds=duration_seconds,
            study_date=study_date,
            timezone_offset_minutes=-480,
            source="pomodoro",
        )
        db.session.add(session)
        db.session.commit()
        return session

    return _make


def iso_today():
    return date.today()


def days_from_today(offset):
    return date.today() + timedelta(days=offset)


def utc_now():
    return datetime.utcnow()
