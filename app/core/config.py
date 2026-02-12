# app/core/config.py
"""
Application configuration — loaded once at startup.
All secrets come from environment variables (.env file locally, real env in production).
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Project root ──────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parents[2]

# ── LLM ───────────────────────────────────────────────────────────────────────
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_TEMPERATURE: float = float(os.getenv("GROQ_TEMPERATURE", "0.3"))
GROQ_MAX_TOKENS: int = int(os.getenv("GROQ_MAX_TOKENS", "1500"))
GROQ_TIMEOUT: int = int(os.getenv("GROQ_TIMEOUT", "45"))

# ── Embeddings ────────────────────────────────────────────────────────────────
EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# ── Paths ─────────────────────────────────────────────────────────────────────
FAISS_INDEX_PATH: Path = BASE_DIR / os.getenv("FAISS_INDEX_DIR", "faiss_index")
DOCUMENTS_PATH: Path = BASE_DIR / os.getenv("DOCUMENTS_DIR", "data/documents")
UPLOAD_DIR: Path = BASE_DIR / os.getenv("UPLOAD_DIR", "uploads")

# ── RAG ───────────────────────────────────────────────────────────────────────
CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "100"))
RAG_TOP_K: int = int(os.getenv("RAG_TOP_K", "4"))
RAG_MIN_SCORE: float = float(os.getenv("RAG_MIN_SCORE", "0.6"))
MAX_HISTORY_LENGTH: int = int(os.getenv("MAX_HISTORY_LENGTH", "6"))

# ── App ───────────────────────────────────────────────────────────────────────
APP_TITLE: str = "SkyBot"
APP_DESCRIPTION: str = "Assistant IA RAG — posez vos questions sur vos documents"
APP_VERSION: str = "1.0.0"
ALLOWED_EXTENSIONS: frozenset = frozenset({".txt", ".pdf"})


def _ensure_dirs() -> None:
    """Create required directories if they don't exist."""
    for d in (FAISS_INDEX_PATH, UPLOAD_DIR):
        d.mkdir(parents=True, exist_ok=True)


def validate() -> None:
    """Raise at startup if the configuration is invalid."""
    if not GROQ_API_KEY:
        raise EnvironmentError(
            "GROQ_API_KEY is missing. "
            "Copy .env.example to .env and fill in your key."
        )
    _ensure_dirs()
