# ==========================================================
# 🧠 NARYAN AI — BACKEND ENTRY POINT
#    Author: Subham Moharana
#    Purpose: Engineering AI Study Assistant — Powered by BTechX
#    College: CV Raman Global University (CGU Odisha)
# ==========================================================
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import logging
from flask import Flask, send_from_directory, redirect
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("NARYAN_AI")

from database import init_db
from chat     import chat_bp
from notes    import notes_bp
from pyq      import pyq_bp
from files    import files_bp
from auth     import auth_bp

# ── App ────────────────────────────────────────────────────
FRONTEND = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")
app = Flask(__name__, static_folder=FRONTEND, static_url_path="")
app.secret_key = os.getenv("SECRET_KEY", "narayan-ai-secret-btechx-2024")
CORS(app, supports_credentials=True)

# ── Blueprints ─────────────────────────────────────────────
app.register_blueprint(auth_bp,  url_prefix="/api/auth")
app.register_blueprint(chat_bp,  url_prefix="/api")
app.register_blueprint(notes_bp, url_prefix="/api")
app.register_blueprint(pyq_bp,   url_prefix="/api")
app.register_blueprint(files_bp, url_prefix="/api")

# ── Serve frontend pages ───────────────────────────────────
@app.route("/")
def index():
    return send_from_directory(FRONTEND, "login.html")

@app.route("/chat")
def chat_page():
    return send_from_directory(FRONTEND, "index.html")

@app.route("/register")
def register_page():
    return send_from_directory(FRONTEND, "register.html")

@app.route("/reset-password")
def reset_page():
    return send_from_directory(FRONTEND, "reset_password.html")

# ── Health ─────────────────────────────────────────────────
@app.route("/health")
def health():
    from vector_store import vector_store
    from datetime import datetime
    return {
        "status":    "ok",
        "time":      datetime.now().isoformat(),
        "kb_chunks": len(vector_store.texts),
        "provider":  "Groq"
    }

# ── Boot ───────────────────────────────────────────────────
if __name__ == "__main__":
    logger.info("🧠 NARYAN AI — Powered by BTechX — Starting up…")
    init_db()

    from ingest_files import ingest_all
    ingest_all()

    port = int(os.getenv("PORT", 5000))
    logger.info(f"   Listening on http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=os.getenv("DEBUG", "false").lower() == "true")
