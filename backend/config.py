import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "NoteWave AI Knowledge Hub"
    VERSION: str = "2.1.0"
    
    BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", os.path.join(BASE_DIR, "documents"))
    CHROMA_DIR: str = os.getenv("CHROMA_DIR", os.path.join(BASE_DIR, "chroma_db"))
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'notewave.db')}")
    
    # Models
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "models/gemini-embedding-001")
    EMBEDDING_DIM: int = int(os.getenv("EMBEDDING_DIM", "768"))
    EMBED_CACHE_MAXSIZE: int = int(os.getenv("EMBED_CACHE_MAXSIZE", "4096"))
    
    # Reranker
    RERANKER_MODEL: str = os.getenv("RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
    RERANKER_ENABLED: bool = os.getenv("RERANKER_ENABLED", "true").lower() in ("true", "1", "yes")
    
    # Chunking & Retrieval Parameters
    PARENT_CHUNK_SIZE: int = int(os.getenv("PARENT_CHUNK_SIZE", "1400"))
    CHILD_CHUNK_SIZE: int = int(os.getenv("CHILD_CHUNK_SIZE", "350"))
    CHILD_CHUNK_OVERLAP: int = int(os.getenv("CHILD_CHUNK_OVERLAP", "60"))
    
    TOP_K_CANDIDATES: int = int(os.getenv("TOP_K_CANDIDATES", "20"))
    TOP_K_FINAL: int = int(os.getenv("TOP_K_FINAL", "5"))
    RRF_K: int = int(os.getenv("RRF_K", "60"))
    
    # Upload limits
    MAX_UPLOAD_SIZE_BYTES: int = int(os.getenv("MAX_UPLOAD_SIZE_BYTES", str(50 * 1024 * 1024)))
    MAX_PAGES_LIMIT: int = int(os.getenv("MAX_PAGES_LIMIT", "250"))
    
    # Local Ollama fallback
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen3:4b")
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "auto").strip().lower()
    
    # CORS
    CORS_ORIGINS: List[str] = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000").split(",")
        if origin.strip()
    ]

settings = Settings()
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.CHROMA_DIR, exist_ok=True)
