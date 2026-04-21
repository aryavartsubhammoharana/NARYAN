# ==========================================================
# 💬 NARYAN AI — CHAT ROUTES
# ==========================================================

import time
import logging
from flask import Blueprint, request, jsonify
from database import get_db
from rag_pipeline import generate_response

logger  = logging.getLogger("NARYAN_AI.chat")
chat_bp = Blueprint("chat", __name__)

# Simple in-memory rate limiter
_limits: dict = {}
RATE_LIMIT  = int(10)
RATE_WINDOW = int(60)


def _check_rate(ip: str) -> bool:
    now = time.time()
    _limits.setdefault(ip, [])
    _limits[ip] = [t for t in _limits[ip] if now - t < RATE_WINDOW]
    if len(_limits[ip]) >= RATE_LIMIT:
        return False
    _limits[ip].append(now)
    return True


@chat_bp.route("/chat", methods=["POST"])
def chat():
    ip = request.remote_addr
    if not _check_rate(ip):
        return jsonify({"error": "Rate limit exceeded. Please wait 60 seconds."}), 429

    body       = request.json or {}
    message    = body.get("message", "").strip()
    history    = body.get("history", [])
    session_id = body.get("session_id", "anon")
    user_id    = body.get("user_id", 0)

    if not message:
        return jsonify({"error": "message is required"}), 400

    try:
        result = generate_response(message, history, user_id=user_id, session_id=session_id)
    except Exception as e:
        logger.error(f"Generation error: {e}")
        return jsonify({"error": str(e)}), 502

    # Persist to DB
    try:
        with get_db() as db:
            db.execute(
                "INSERT INTO chat_history (user_id, session_id, question, answer, intent, subject) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, session_id, message, result["reply"],
                 result["intent"], result["subject"])
            )
    except Exception as e:
        logger.warning(f"DB write failed: {e}")

    return jsonify(result)


@chat_bp.route("/history", methods=["GET"])
def history():
    session_id = request.args.get("session_id", "anon")
    limit      = min(int(request.args.get("limit", 20)), 100)
    try:
        with get_db() as db:
            db.execute(
                "SELECT question, answer, intent, subject, created_at "
                "FROM chat_history WHERE session_id=? ORDER BY created_at DESC LIMIT ?",
                (session_id, limit)
            )
            rows = db.fetchall()
        return jsonify({"history": [dict(r) for r in rows]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
