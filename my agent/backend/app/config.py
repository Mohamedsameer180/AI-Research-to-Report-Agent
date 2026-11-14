import os
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings

_BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    PROJECT_NAME: str = "TP01: AI Research Paper Intelligence Platform"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api"

    # Directory Paths
    BASE_DIR: Path = _BACKEND_DIR
    UPLOAD_DIR: Path = _BACKEND_DIR / "uploads"
    OUTPUT_DIR: Path = _BACKEND_DIR / "outputs"
    CHROMA_PERSIST_DIR: Path = _BACKEND_DIR / "chroma_db"
    BM25_INDEX_DIR: Path = _BACKEND_DIR / "bm25_indices"

    # Database
    DATABASE_URL: str = f"sqlite:///{_BACKEND_DIR / 'research_platform.db'}"

    # Google Gemini & Model Settings
    GOOGLE_API_KEY: str = Field(default="")
    GEMINI_API_KEY: str = Field(default="")
    GEMINI_MODEL: str = "gemini-2.0-flash"
    
    # RAG & Embedding Settings
    EMBEDDING_PROVIDER: str = "sentence-transformers"
    EMBEDDING_MODEL_NAME: str = "BAAI/bge-small-en-v1.5"
    CROSS_ENCODER_MODEL_NAME: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    CHUNK_SIZE_TOKENS: int = 400
    CHUNK_OVERLAP_TOKENS: int = 60
    MAX_DOCUMENTS_PER_WORKSPACE: int = 15
    MAX_FILE_SIZE_BYTES: int = 25 * 1024 * 1024  # 25 MB

    # Tenant Defaults
    DEFAULT_WORKSPACE_ID: str = "default_workspace"
    DEFAULT_USER_ID: str = "local_user"

    class Config:
        env_file = str(_BACKEND_DIR / ".env")
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()

# Ensure directories exist
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
settings.CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)
settings.BM25_INDEX_DIR.mkdir(parents=True, exist_ok=True)

