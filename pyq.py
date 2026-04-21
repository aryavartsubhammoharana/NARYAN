# ==========================================================
# 📝 NARYAN AI — PYQ (Previous Year Questions) ROUTES
# ==========================================================

import logging
from flask import Blueprint, request, jsonify
from vector_store import vector_store

logger = logging.getLogger("NARYAN_AI.pyq")
pyq_bp = Blueprint("pyq", __name__)


@pyq_bp.route("/pyq/search", methods=["GET", "POST"])
def search_pyq():
    """Search PYQs by topic + optional subject."""
    if request.method == "POST":
        body    = request.json or {}
        query   = body.get("query", "").strip()
        subject = body.get("subject", "")
        k       = int(body.get("k", 6))
    else:
        query   = request.args.get("q", "").strip()
        subject = request.args.get("subject", "")
        k       = int(request.args.get("k", 6))

    if not query:
        return jsonify({"error": "query is required"}), 400

    all_results = vector_store.search(query, k=k * 2, subject_filter=subject)
    pyq_results = [r for r in all_results if r.get("type") == "pyq"][:k]

    if not pyq_results:
        # Fall back to general search
        pyq_results = all_results[:k]

    return jsonify({"results": pyq_results, "total": len(pyq_results)})


@pyq_bp.route("/pyq/subjects", methods=["GET"])
def list_pyq_subjects():
    subjects = sorted(set(
        m.get("subject", "") for m in vector_store.meta if m.get("type") == "pyq"
    ))
    return jsonify({"subjects": subjects})
