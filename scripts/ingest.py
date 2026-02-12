#!/usr/bin/env python
# scripts/ingest.py
"""
CLI script — pre-ingest all documents from data/documents/ and save the FAISS index.

Usage:
    python scripts/ingest.py
or via Makefile:
    make ingest
"""

import logging
import sys
from pathlib import Path

# Ensure project root is on sys.path when run directly
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

logging.basicConfig(level=logging.INFO, format="%(levelname)s — %(message)s")
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    from app.core.config import validate

    try:
        validate()
    except EnvironmentError as exc:
        logger.error("%s", exc)
        sys.exit(1)

    from app.services.ingest import ingest_directory

    try:
        vs = ingest_directory(save_to_disk=True)
        logger.info("Ingestion complete. Index saved.")
    except ValueError as exc:
        logger.error("Ingestion error: %s", exc)
        sys.exit(1)
