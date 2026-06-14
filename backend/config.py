import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "study-system-dev-secret")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root:123456@localhost:3306/study_system?charset=utf8mb4",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    AUTO_CREATE_TABLES = os.getenv("AUTO_CREATE_TABLES", "true").lower() == "true"

    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", str(BASE_DIR / "uploads"))
    CHROMA_DIR = os.getenv("CHROMA_DIR", str(BASE_DIR / "chroma_store"))
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", str(30 * 1024 * 1024)))
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

    AI_BASE_URL = os.getenv("AI_BASE_URL", "").rstrip("/")
    AI_API_KEY = os.getenv("AI_API_KEY", "")
    CHAT_BASE_URL = os.getenv("CHAT_BASE_URL", AI_BASE_URL).rstrip("/")
    CHAT_API_KEY = os.getenv("CHAT_API_KEY", AI_API_KEY)
    CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-4o-mini")
    CHAT_WIRE_API = os.getenv("CHAT_WIRE_API", "chat_completions")
    CHAT_REASONING_EFFORT = os.getenv("CHAT_REASONING_EFFORT", "high")
    CHAT_DISABLE_RESPONSE_STORAGE = os.getenv("CHAT_DISABLE_RESPONSE_STORAGE", "true").lower() == "true"
    TEXT_EMBEDDING_BASE_URL = os.getenv("TEXT_EMBEDDING_BASE_URL", "").rstrip("/")
    TEXT_EMBEDDING_API_KEY = os.getenv("TEXT_EMBEDDING_API_KEY", "")
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    RAG_TOP_K = int(os.getenv("RAG_TOP_K", "5"))
    TEXT_VECTOR_COLLECTION = os.getenv("TEXT_VECTOR_COLLECTION", "study_materials")
    VISUAL_VECTOR_COLLECTION = os.getenv("VISUAL_VECTOR_COLLECTION", "study_visual_assets")

    MULTIMODAL_RAG_ENABLED = os.getenv("MULTIMODAL_RAG_ENABLED", "true").lower() == "true"
    MULTIMODAL_EMBEDDING_URL = os.getenv(
        "MULTIMODAL_EMBEDDING_URL",
        "https://dashscope.aliyuncs.com/api/v1/services/embeddings/multimodal-embedding/multimodal-embedding",
    ).rstrip("/")
    MULTIMODAL_EMBEDDING_API_KEY = os.getenv("MULTIMODAL_EMBEDDING_API_KEY", os.getenv("DASHSCOPE_API_KEY", ""))
    MULTIMODAL_EMBEDDING_MODEL = os.getenv("MULTIMODAL_EMBEDDING_MODEL", "qwen3-vl-embedding")
    MULTIMODAL_EMBEDDING_DIMENSION = int(os.getenv("MULTIMODAL_EMBEDDING_DIMENSION", "1024"))
    MULTIMODAL_TOP_K = int(os.getenv("MULTIMODAL_TOP_K", "3"))
    MAX_VISUAL_ASSETS_PER_MATERIAL = int(os.getenv("MAX_VISUAL_ASSETS_PER_MATERIAL", "40"))
    VISUAL_IMAGE_MAX_SIDE = int(os.getenv("VISUAL_IMAGE_MAX_SIDE", "1600"))
    VISUAL_IMAGE_MAX_BYTES = int(os.getenv("VISUAL_IMAGE_MAX_BYTES", str(4 * 1024 * 1024)))
    PDF_RENDER_DPI = int(os.getenv("PDF_RENDER_DPI", "120"))
