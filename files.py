# ==========================================================
# 📎 NARYAN AI — FILE UPLOAD ROUTES
# ==========================================================

import os
import logging
from flask import Blueprint, request, jsonify
from file_loader  import load_file, chunk_text
from vector_store import vector_store
from database import get_db

logger   = logging.getLogger("NARYAN_AI.files")
files_bp = Blueprint("files", __name__)

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
MAX_MB     = int(os.getenv("MAX_FILE_MB", 50))
ALLOWED    = {".pdf", ".docx", ".pptx", ".txt", ".md"}


@files_bp.route("/upload", methods=["POST"])
def upload():
    files   = request.files.getlist("files")
    subject = request.form.get("subject", "")
    doc_type = request.form.get("type", "notes")   # "notes" | "pyq"

    if not files:
        return jsonify({"error": "No files provided"}), 400

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    loaded, errors = [], []

    for f in files:
        ext = os.path.splitext(f.filename)[1].lower()
        if ext not in ALLOWED:
            errors.append(f"{f.filename}: unsupported type")
            continue

        data = f.read()
        if len(data) / (1024 * 1024) > MAX_MB:
            errors.append(f"{f.filename}: exceeds {MAX_MB} MB")
            continue
        f.seek(0)

        save_path = os.path.join(UPLOAD_DIR, f.filename)
        f.save(save_path)

        text   = load_file(save_path)
        chunks = chunk_text(text)
        meta   = [{"source": f.filename, "subject": subject, "type": doc_type, "path": save_path}
                  for _ in chunks]
        vector_store.add_chunks(chunks, meta)

        # Record in DB
        try:
            with get_db() as db:
                db.execute(
                    "INSERT INTO files (subject, file_name, file_path, file_type) VALUES (?,?,?,?)",
                    (subject, f.filename, save_path, doc_type)
                )
        except Exception as e:
            logger.warning(f"DB write failed for {f.filename}: {e}")

        loaded.append(f.filename)
        logger.info(f"Uploaded & indexed: {f.filename} ({len(chunks)} chunks)")

    return jsonify({
        "loaded":       loaded,
        "errors":       errors,
        "total_chunks": len(vector_store.texts),
    })


@files_bp.route("/files", methods=["GET"])
def list_files():
    try:
        with get_db() as db:
            db.execute("SELECT id, subject, file_name, file_type, added_at FROM files ORDER BY added_at DESC")
            rows = db.fetchall()
        return jsonify({"files": [dict(r) for r in rows]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
