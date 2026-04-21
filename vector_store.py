# ==========================================================
# 🔍 NARYAN AI — VECTOR STORE (TF-IDF semantic search)
#    Drop-in upgrade path to FAISS/Chroma described below.
# ==========================================================

import os
import logging
import pickle
from typing import List, Dict, Optional

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger("NARYAN_AI.vector_store")
INDEX_PATH = os.getenv("VECTOR_INDEX_PATH", "vector_index.pkl")


class VectorStore:
    def __init__(self):
        self.texts:       List[str]  = []
        self.meta:        List[dict] = []
        self.vectorizer:  Optional[TfidfVectorizer] = None
        self.matrix = None
        self._load_from_disk()

    # ── Indexing ───────────────────────────────────────────
    def add_chunks(self, chunks: List[str], metadata: List[dict]):
        """Add new text chunks with metadata and rebuild index."""
        self.texts.extend(chunks)
        self.meta.extend(metadata)
        self._build_index()
        self._save_to_disk()

    def _build_index(self):
        if not self.texts:
            return
        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            max_features=50_000
        )
        self.matrix = self.vectorizer.fit_transform(self.texts)
        logger.info(f"Index rebuilt: {len(self.texts)} chunks")

    # ── Search ─────────────────────────────────────────────
    def search(self, query: str, k: int = 5, subject_filter: str = "") -> List[Dict]:
        """Return top-k relevant chunks for the query."""
        if self.vectorizer is None or self.matrix is None:
            return []
        qv     = self.vectorizer.transform([query])
        scores = cosine_similarity(qv, self.matrix).flatten()

        results = []
        for idx in scores.argsort()[::-1]:
            if scores[idx] < 0.05:
                break
            meta = self.meta[idx]
            if subject_filter and meta.get("subject", "").lower() != subject_filter.lower():
                continue
            results.append({
                "text":    self.texts[idx],
                "score":   round(float(scores[idx]) * 100, 2),
                "source":  meta.get("source", "unknown"),
                "subject": meta.get("subject", ""),
                "type":    meta.get("type", "notes"),
            })
            if len(results) >= k:
                break
        return results

    # ── Persistence ────────────────────────────────────────
    def _save_to_disk(self):
        try:
            with open(INDEX_PATH, "wb") as f:
                pickle.dump({
                    "texts": self.texts,
                    "meta":  self.meta,
                    "vectorizer": self.vectorizer,
                    "matrix": self.matrix,
                }, f)
        except Exception as e:
            logger.warning(f"Could not save index: {e}")

    def _load_from_disk(self):
        if not os.path.exists(INDEX_PATH):
            return
        try:
            with open(INDEX_PATH, "rb") as f:
                data = pickle.load(f)
            self.texts      = data["texts"]
            self.meta       = data["meta"]
            self.vectorizer = data["vectorizer"]
            self.matrix     = data["matrix"]
            logger.info(f"Loaded existing index: {len(self.texts)} chunks")
        except Exception as e:
            logger.warning(f"Could not load index: {e}")

    def clear(self):
        self.texts, self.meta, self.vectorizer, self.matrix = [], [], None, None
        if os.path.exists(INDEX_PATH):
            os.remove(INDEX_PATH)


# Singleton
vector_store = VectorStore()

# ==========================================================
# UPGRADE PATH — FAISS (optional, for large knowledge bases)
# ==========================================================
# To switch to FAISS:
#
# pip install faiss-cpu sentence-transformers
#
# Replace VectorStore with:
#   from sentence_transformers import SentenceTransformer
#   import faiss, numpy as np
#
#   model = SentenceTransformer("all-MiniLM-L6-v2")
#   index = faiss.IndexFlatL2(384)
#
# add_chunks  → encode → index.add(vectors)
# search      → encode query → index.search(qv, k)
# ==========================================================
