# app/api/routes.py
"""
HTTP route definitions — kept thin; all logic lives in services.
"""

import logging
import shutil
from pathlib import Path

from fastapi import APIRouter, File, Form, Header, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse

from app.core.config import ALLOWED_EXTENSIONS, UPLOAD_DIR
from app.services.chatbot import RAGChatbot

logger = logging.getLogger(__name__)

router = APIRouter()

# Shared chatbot instance (one per process — single-user app)
_chatbot: RAGChatbot = RAGChatbot()


# ── HTML views ────────────────────────────────────────────────────────────────


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Render the main chat page."""
    return request.app.state.templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "answer": None,
            "question": None,
            "upload_message": None,
            "is_ready": _chatbot.is_ready,
        },
    )


@router.post("/ask")
async def ask(
    request: Request,
    question: str = Form(...),
    accept: str = Header(default="text/html"),
):
    """
    Handle a chat question.
    - Returns JSON when Accept: application/json (AJAX fetch calls).
    - Returns rendered HTML otherwise (progressive-enhancement fallback).
    """
    question = question.strip()
    if not question:
        answer = "⚠️ Veuillez saisir une question."
    else:
        answer = _chatbot.ask(question)

    if "application/json" in accept:
        return JSONResponse({"answer": answer, "question": question})

    return request.app.state.templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "answer": answer,
            "question": question,
            "upload_message": None,
            "is_ready": _chatbot.is_ready,
        },
    )


# ── JSON API endpoints ────────────────────────────────────────────────────────


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    save_index: bool = Form(False),
):
    """
    Upload a document (TXT or PDF), ingest it, and rebuild the chatbot index.

    Returns:
        200 {"ok": true, "message": "..."} on success
        400 {"ok": false, "message": "..."} on invalid input
        500 {"ok": false, "message": "..."} on ingestion error
    """
    filename = Path(file.filename).name  # strip any path component (security)
    ext = Path(filename).suffix.lower()

    if ext not in ALLOWED_EXTENSIONS:
        return JSONResponse(
            {"ok": False, "message": f"Extension non supportée : {ext}. Formats acceptés : .txt, .pdf"},
            status_code=400,
        )

    saved_path = UPLOAD_DIR / filename
    try:
        with saved_path.open("wb") as buf:
            shutil.copyfileobj(file.file, buf)
    except OSError:
        logger.exception("Failed to save uploaded file: %s", saved_path)
        return JSONResponse(
            {"ok": False, "message": "Impossible de sauvegarder le fichier."},
            status_code=500,
        )

    try:
        _chatbot.rebuild_from_file(saved_path, save_to_disk=save_index)
        return JSONResponse(
            {"ok": True, "message": f"✅ Fichier « {filename} » indexé avec succès."}
        )
    except Exception as exc:
        logger.exception("Ingestion failed for: %s", saved_path)
        return JSONResponse(
            {"ok": False, "message": f"Erreur d'indexation : {exc}"},
            status_code=500,
        )


@router.get("/status")
async def status():
    """Health check + chatbot readiness."""
    return {"status": "ok", "chatbot": _chatbot.info()}


@router.post("/clear-history")
async def clear_history():
    """Reset the conversation history."""
    _chatbot.clear_history()
    return {"ok": True, "message": "Historique effacé."}
