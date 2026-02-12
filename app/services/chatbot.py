# app/services/chatbot.py
"""
RAG Chatbot service.
Encapsulates vector search + LLM call + conversation history management.
"""

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

import requests
from langchain_community.vectorstores import FAISS

from app.core.config import (
    GROQ_API_KEY,
    GROQ_MAX_TOKENS,
    GROQ_MODEL,
    GROQ_TEMPERATURE,
    GROQ_TIMEOUT,
    MAX_HISTORY_LENGTH,
    RAG_MIN_SCORE,
    RAG_TOP_K,
)
from app.services.ingest import ingest_file, load_index

logger = logging.getLogger(__name__)

# ── Types ─────────────────────────────────────────────────────────────────────

Turn = tuple[str, str]  # (question, answer)

# ── Groq LLM client ───────────────────────────────────────────────────────────

_GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


def _call_groq(prompt: str) -> str:
    """Call the Groq API and return the assistant message text."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROQ_API_KEY}",
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": GROQ_TEMPERATURE,
        "max_tokens": GROQ_MAX_TOKENS,
        "top_p": 0.9,
        "stream": False,
    }

    try:
        response = requests.post(
            _GROQ_URL, headers=headers, json=payload, timeout=GROQ_TIMEOUT
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    except requests.exceptions.Timeout:
        logger.warning("Groq API request timed out.")
        return "⏳ La requête a pris trop de temps. Veuillez réessayer avec une question plus courte."

    except requests.exceptions.HTTPError as exc:
        logger.error("Groq API HTTP error: %s — %s", exc.response.status_code, exc.response.text)
        return f"⚠️ Erreur API ({exc.response.status_code}). Veuillez réessayer."

    except Exception:
        logger.exception("Unexpected error calling Groq API.")
        return "❌ Une erreur inattendue s'est produite. Veuillez réessayer."


# ── Prompt builder ────────────────────────────────────────────────────────────


def _build_prompt(question: str, context_docs: list, history: list[Turn]) -> str:
    """Assemble the final prompt sent to the LLM."""

    # Context passages
    passages = []
    for i, doc in enumerate(context_docs, start=1):
        source = ""
        if getattr(doc, "metadata", {}).get("source"):
            source = f" [Source: {os.path.basename(doc.metadata['source'])}]"
        passages.append(f"--- Extrait {i}{source} ---\n{doc.page_content}")
    context_block = "\n\n".join(passages)

    # Conversation history (last 3 turns)
    history_block = ""
    if history:
        lines = []
        for idx, (q, a) in enumerate(history[-3:], start=1):
            lines.append(f"Q{idx}: {q}\nA{idx}: {a}")
        history_block = "HISTORIQUE RÉCENT:\n" + "\n\n".join(lines) + "\n\n"

    return f"""Tu es SkyBot, un assistant IA spécialisé dans l'analyse de documents.

INSTRUCTIONS:
1. Réponds UNIQUEMENT en te basant sur le CONTEXTE fourni ci-dessous.
2. Si l'information est absente du contexte, réponds : "Je ne trouve pas cette information dans le document."
3. Sois précis, concis et factuel. Ne jamais inventer ou extrapoler.
4. Cite tes sources quand c'est pertinent.
5. Structure ta réponse clairement.

{history_block}CONTEXTE DOCUMENTAIRE:
{context_block}

QUESTION: {question}

RÉPONSE (basée uniquement sur le contexte):"""


# ── Chatbot ───────────────────────────────────────────────────────────────────


@dataclass
class RAGChatbot:
    """
    Stateful RAG chatbot.
    - Loads a persisted FAISS index on startup (if available).
    - Can rebuild the index from a new uploaded file.
    - Maintains a short conversation history per instance.
    """

    _vectorstore: FAISS | None = field(default=None, init=False, repr=False)
    _history: list[Turn] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self) -> None:
        self._vectorstore = load_index()
        status = "loaded" if self._vectorstore else "not found — waiting for upload"
        logger.info("RAGChatbot initialised. Index status: %s", status)

    # ── Public interface ──────────────────────────────────────────────────────

    @property
    def is_ready(self) -> bool:
        return self._vectorstore is not None

    def rebuild_from_file(self, file_path: Path, save_to_disk: bool = False) -> None:
        """Replace the current vectorstore with a new one built from *file_path*."""
        self._vectorstore = ingest_file(file_path, save_to_disk=save_to_disk)
        logger.info("Vectorstore rebuilt from: %s", file_path)

    def ask(self, question: str, k: int = RAG_TOP_K) -> str:
        """Answer *question* using RAG; return a plain string."""
        if not self.is_ready:
            return (
                "⚠️ Aucun document n'a été importé. "
                "Veuillez importer un fichier via la zone d'upload."
            )

        docs = self._retrieve(question, k)
        if not docs:
            return "🔍 Je n'ai pas trouvé d'informations pertinentes dans le document pour répondre à votre question."

        prompt = _build_prompt(question, docs, self._history)
        answer = _call_groq(prompt)
        self._add_to_history(question, answer)
        return answer

    def clear_history(self) -> None:
        """Reset conversation history."""
        self._history.clear()
        logger.info("Conversation history cleared.")

    def info(self) -> dict:
        """Return metadata about the loaded vectorstore."""
        if not self.is_ready:
            return {"status": "no_document"}

        fragment_count: int | None = None
        try:
            docstore = getattr(self._vectorstore, "docstore", None)
            if docstore and hasattr(docstore, "_dict"):
                fragment_count = len(docstore._dict)
        except Exception:
            pass

        return {
            "status": "ready",
            "fragment_count": fragment_count,
            "embedding_model": "all-MiniLM-L6-v2",
        }

    # ── Private helpers ───────────────────────────────────────────────────────

    def _retrieve(self, question: str, k: int) -> list:
        """Run similarity search; fall back to plain search if scored search fails."""
        try:
            pairs = self._vectorstore.similarity_search_with_score(question, k=k)
            docs = [doc for doc, score in pairs if score >= RAG_MIN_SCORE]
            if docs:
                return docs
            logger.debug("All scores below threshold %.2f — falling back.", RAG_MIN_SCORE)
        except Exception:
            logger.warning("Scored similarity search failed; using plain search.", exc_info=True)

        return self._vectorstore.similarity_search(question, k=k)

    def _add_to_history(self, question: str, answer: str) -> None:
        self._history.append((question, answer))
        if len(self._history) > MAX_HISTORY_LENGTH:
            self._history = self._history[-MAX_HISTORY_LENGTH:]
