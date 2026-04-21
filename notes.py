# ==========================================================
# 📚 NARYAN AI — NOTES ROUTES
# ==========================================================

import logging
from flask import Blueprint, request, jsonify
from vector_store import vector_store

logger   = logging.getLogger("NARYAN_AI.notes")
notes_bp = Blueprint("notes", __name__)


@notes_bp.route("/notes/search", methods=["GET", "POST"])
def search_notes():
    """Search notes by query + optional subject filter."""
    if request.method == "POST":
        body    = request.json or {}
        query   = body.get("query", "").strip()
        subject = body.get("subject", "")
        k       = int(body.get("k", 5))
    else:
        query   = request.args.get("q", "").strip()
        subject = request.args.get("subject", "")
        k       = int(request.args.get("k", 5))

    if not query:
        return jsonify({"error": "query is required"}), 400

    results = vector_store.search(query, k=k, subject_filter=subject)
    # Filter to notes only
    notes = [r for r in results if r.get("type") in ("notes", "")]
    return jsonify({"results": notes, "total": len(notes)})


@notes_bp.route("/notes/subjects", methods=["GET"])
def list_subjects():
    """List all subjects present in the knowledge base."""
    subjects = sorted(set(m.get("subject", "") for m in vector_store.meta if m.get("type") == "notes"))
    return jsonify({"subjects": subjects})
