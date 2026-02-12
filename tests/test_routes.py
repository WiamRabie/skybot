# tests/test_routes.py
"""
Smoke tests for the HTTP API.
Run with:  pytest tests/ -v
"""

import os
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# ── Set a dummy API key before importing the app ──────────────────────────────
os.environ.setdefault("GROQ_API_KEY", "test-key-placeholder")

from app.main import app  # noqa: E402  (import after env setup)

client = TestClient(app)


# ── Home page ─────────────────────────────────────────────────────────────────


def test_home_returns_200():
    response = client.get("/")
    assert response.status_code == 200
    assert "SkyBot" in response.text


# ── Status endpoint ───────────────────────────────────────────────────────────


def test_status_ok():
    response = client.get("/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "chatbot" in data


# ── /ask without a document ───────────────────────────────────────────────────


def test_ask_no_document_returns_warning():
    """When no document is loaded, the chatbot should return a warning message."""
    response = client.post(
        "/ask",
        data={"question": "Quel est le nombre de passagers ?"},
        headers={"Accept": "application/json"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    # Should warn about missing document
    assert "document" in data["answer"].lower() or "import" in data["answer"].lower()


def test_ask_empty_question():
    """Empty question should return a warning, not crash."""
    response = client.post(
        "/ask",
        data={"question": "   "},
        headers={"Accept": "application/json"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data


# ── /upload ───────────────────────────────────────────────────────────────────


def test_upload_unsupported_extension():
    fake_file = BytesIO(b"content")
    response = client.post(
        "/upload",
        files={"file": ("document.docx", fake_file, "application/octet-stream")},
        data={"save_index": "false"},
    )
    assert response.status_code == 400
    data = response.json()
    assert data["ok"] is False
    assert "extension" in data["message"].lower() or "support" in data["message"].lower()


@patch("app.api.routes._chatbot.rebuild_from_file")
def test_upload_valid_txt(mock_rebuild):
    """Valid .txt upload should call rebuild_from_file and return ok=True."""
    mock_rebuild.return_value = None
    fake_file = BytesIO(b"Hello airport data.")
    response = client.post(
        "/upload",
        files={"file": ("test.txt", fake_file, "text/plain")},
        data={"save_index": "false"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    mock_rebuild.assert_called_once()


# ── Clear history ─────────────────────────────────────────────────────────────


def test_clear_history():
    response = client.post("/clear-history")
    assert response.status_code == 200
    assert response.json()["ok"] is True
