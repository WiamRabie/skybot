# app/main.py
"""
FastAPI application factory.
Run with:  uvicorn app.main:app --reload
"""

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api.routes import router
from app.core.config import APP_DESCRIPTION, APP_TITLE, APP_VERSION, validate

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── Validate config at import time (raises if GROQ_API_KEY is missing) ────────
validate()

# ── App ───────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent

app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Static files & templates
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
app.state.templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Routes
app.include_router(router)

logger.info("SkyBot v%s started.", APP_VERSION)
