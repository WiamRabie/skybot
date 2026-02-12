# app/services/ingest.py
"""
Document ingestion service.
Handles loading, splitting, and embedding documents into a FAISS vector store.
"""

import logging
from pathlib import Path

from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader, TextLoader
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    DOCUMENTS_PATH,
    EMBEDDING_MODEL,
    FAISS_INDEX_PATH,
)

logger = logging.getLogger(__name__)


def _get_embeddings() -> SentenceTransformerEmbeddings:
    return SentenceTransformerEmbeddings(model_name=EMBEDDING_MODEL)


def _split_documents(docs: list[Document]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    chunks = splitter.split_documents(docs)
    logger.info("Split %d document(s) into %d chunk(s).", len(docs), len(chunks))
    return chunks


def _load_file(file_path: Path) -> list[Document]:
    """Load a single TXT or PDF file."""
    ext = file_path.suffix.lower()
    if ext == ".txt":
        return TextLoader(str(file_path), encoding="utf-8").load()
    if ext == ".pdf":
        return PyPDFLoader(str(file_path)).load()
    raise ValueError(f"Unsupported file extension: {ext!r}")


# ── Public API ────────────────────────────────────────────────────────────────


def ingest_directory(save_to_disk: bool = True) -> FAISS:
    """
    Ingest all TXT and PDF documents from DOCUMENTS_PATH.
    Returns a FAISS vectorstore (and optionally saves it to disk).
    """
    logger.info("Starting directory ingestion from: %s", DOCUMENTS_PATH)

    docs: list[Document] = []
    for glob, cls in (("**/*.txt", TextLoader), ("**/*.pdf", PyPDFLoader)):
        loader = DirectoryLoader(str(DOCUMENTS_PATH), glob=glob, loader_cls=cls)
        loaded = loader.load()
        docs.extend(loaded)
        logger.info("Loaded %d file(s) matching %s.", len(loaded), glob)

    if not docs:
        raise ValueError(f"No documents found in {DOCUMENTS_PATH}")

    chunks = _split_documents(docs)
    embeddings = _get_embeddings()
    vectorstore = FAISS.from_documents(chunks, embeddings)

    if save_to_disk:
        FAISS_INDEX_PATH.mkdir(parents=True, exist_ok=True)
        vectorstore.save_local(str(FAISS_INDEX_PATH))
        logger.info("FAISS index saved to: %s", FAISS_INDEX_PATH)

    return vectorstore


def ingest_file(file_path: Path, save_to_disk: bool = False) -> FAISS:
    """
    Ingest a single file (TXT or PDF).
    Returns an in-memory FAISS vectorstore.
    Optionally overwrites the persisted index.
    """
    logger.info("Ingesting file: %s (save_to_disk=%s)", file_path, save_to_disk)

    docs = _load_file(file_path)
    if not docs:
        raise ValueError(f"No content could be extracted from {file_path}")

    chunks = _split_documents(docs)
    embeddings = _get_embeddings()
    vectorstore = FAISS.from_documents(chunks, embeddings)

    if save_to_disk:
        FAISS_INDEX_PATH.mkdir(parents=True, exist_ok=True)
        vectorstore.save_local(str(FAISS_INDEX_PATH))
        logger.info("FAISS index saved to: %s", FAISS_INDEX_PATH)

    return vectorstore


def load_index() -> FAISS | None:
    """
    Load a persisted FAISS index from disk.
    Returns None if no index exists yet.
    """
    if not FAISS_INDEX_PATH.exists() or not any(FAISS_INDEX_PATH.iterdir()):
        logger.info("No persisted FAISS index found.")
        return None

    try:
        embeddings = _get_embeddings()
        vs = FAISS.load_local(
            str(FAISS_INDEX_PATH),
            embeddings,
            allow_dangerous_deserialization=True,
        )
        logger.info("FAISS index loaded from: %s", FAISS_INDEX_PATH)
        return vs
    except Exception:
        logger.exception("Failed to load FAISS index.")
        return None
