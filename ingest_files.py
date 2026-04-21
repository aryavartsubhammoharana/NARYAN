# ==========================================================
# 🗃️  NARYAN AI — KNOWLEDGE BASE INGESTION SCRIPT
#     Run once (or on startup) to index all local files.
#     Usage:  python scripts/ingest_files.py
# ==========================================================

import os
import sys
import logging

# Make sure parent directory is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from file_loader  import load_folder
from vector_store import vector_store

logger = logging.getLogger("NARYAN_AI.ingest")
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# ── Knowledge base root ────────────────────────────────────
KB_ROOT = os.getenv(
    "KB_ROOT",
    os.path.join(os.path.dirname(__file__), "..", "..", "knowledge_base")
)
NOTES_DIR = os.path.join(KB_ROOT, "notes")
PYQ_DIR   = os.path.join(KB_ROOT, "pyq")

SUBJECTS = [
    "Basic Electrical Engineering",
    "Introduction to Electrical Engineering",
    "Mathematics 1",
    "Mathematics 2",
    "Physics",
    "Introduction to Mechanical Engineering",
]


def ingest_all():
    """Index all notes and PYQs into the vector store."""
    total_chunks = 0

    # ── Notes ──────────────────────────────────────────────
    if os.path.isdir(NOTES_DIR):
        for subject in SUBJECTS:
            folder = os.path.join(NOTES_DIR, subject)
            if not os.path.isdir(folder):
                continue
            pairs = load_folder(folder, subject=subject, doc_type="notes")
            if pairs:
                texts = [p[0] for p in pairs]
                metas = [p[1] for p in pairs]
                vector_store.add_chunks(texts, metas)
                total_chunks += len(texts)
                logger.info(f"[notes] {subject}: {len(texts)} chunks")
    else:
        logger.warning(f"Notes directory not found: {NOTES_DIR}")

    # ── PYQs ───────────────────────────────────────────────
    if os.path.isdir(PYQ_DIR):
        for subject in SUBJECTS:
            folder = os.path.join(PYQ_DIR, subject)
            if not os.path.isdir(folder):
                continue
            pairs = load_folder(folder, subject=subject, doc_type="pyq")
            if pairs:
                texts = [p[0] for p in pairs]
                metas = [p[1] for p in pairs]
                vector_store.add_chunks(texts, metas)
                total_chunks += len(texts)
                logger.info(f"[pyq]   {subject}: {len(texts)} chunks")
    else:
        logger.warning(f"PYQ directory not found: {PYQ_DIR}")

    logger.info(f"Ingestion complete. Total chunks in store: {len(vector_store.texts)}")
    return total_chunks


if __name__ == "__main__":
    ingest_all()
