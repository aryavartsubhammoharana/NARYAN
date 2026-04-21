# ==========================================================
# 🔐 NARYAN AI — AUTH ROUTES
#    Register · Login · Verify Email · Reset Password
#    Only @cgu-odisha.ac.in emails allowed
# ==========================================================

import os
import re
import uuid
import logging
import hashlib
from datetime import datetime, timedelta
from functools import wraps

from flask import Blueprint, request, jsonify, session

from database import get_db

logger  = logging.getLogger("NARYAN_AI.auth")
auth_bp = Blueprint("auth", __name__)

COLLEGE_DOMAIN = os.getenv("COLLEGE_DOMAIN", "cgu-odisha.ac.in")
USE_MYSQL      = os.getenv("USE_MYSQL", "false").lower() == "true"


# ── Helpers ────────────────────────────────────────────────

def _hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def _token() -> str:
    return uuid.uuid4().hex + uuid.uuid4().hex

def _valid_email(email: str) -> bool:
    return bool(re.match(rf"^[\w.\-]+@{re.escape(COLLEGE_DOMAIN)}$", email, re.I))

def _valid_password(pw: str) -> bool:
    return len(pw) >= 8

def _ph(col):
    """Return %s for MySQL, ? for SQLite."""
    return "%s" if USE_MYSQL else "?"

PH = "%s" if USE_MYSQL else "?"


# ── Auth guard (use in chat route if needed) ───────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("user_id"):
            return jsonify({"error": "Unauthorised. Please log in."}), 401
        return f(*args, **kwargs)
    return decorated


# ── REGISTER ───────────────────────────────────────────────

@auth_bp.route("/register", methods=["POST"])
def register():
    data        = request.json or {}
    full_name   = data.get("full_name", "").strip()
    email       = data.get("email", "").strip().lower()
    password    = data.get("password", "")
    branch      = data.get("branch", "").strip()
    roll_number = data.get("roll_number", "").strip()

    # ── Validation ──────────────────────────────────────────
    if not all([full_name, email, password, branch, roll_number]):
        return jsonify({"error": "All fields are required."}), 400

    if not _valid_email(email):
        return jsonify({"error": f"Only @{COLLEGE_DOMAIN} emails are allowed."}), 400

    if not _valid_password(password):
        return jsonify({"error": "Password must be at least 8 characters."}), 400

    token = _token()

    try:
        with get_db() as db:
            db.execute(
                f"INSERT INTO users (full_name, email, password_hash, branch, roll_number, verify_token) "
                f"VALUES ({PH},{PH},{PH},{PH},{PH},{PH})",
                (full_name, email, _hash(password), branch, roll_number, token)
            )
    except Exception as e:
        err = str(e).lower()
        if "unique" in err or "duplicate" in err:
            return jsonify({"error": "Email or Roll Number already registered."}), 409
        logger.error(f"Register DB error: {e}")
        return jsonify({"error": "Registration failed. Please try again."}), 500

    # Send verification email
    try:
        from services.mail_service import send_verification_email
        send_verification_email(email, full_name, token)
    except Exception as e:
        logger.warning(f"Email send failed: {e}")

    return jsonify({
        "message": f"Registered successfully! Please check your email ({email}) to verify your account."
    }), 201


# ── VERIFY EMAIL ───────────────────────────────────────────

@auth_bp.route("/verify/<token>", methods=["GET"])
def verify_email(token):
    try:
        with get_db() as db:
            db.execute(f"SELECT id FROM users WHERE verify_token={PH}", (token,))
            user = db.fetchone()
            if not user:
                return "<h2 style='font-family:sans-serif;color:red'>❌ Invalid or expired verification link.</h2>", 400
            uid = user["id"] if isinstance(user, dict) else user[0]
            db.execute(
                f"UPDATE users SET is_verified=1, verify_token=NULL WHERE id={PH}", (uid,)
            )
    except Exception as e:
        logger.error(f"Verify error: {e}")
        return "<h2 style='font-family:sans-serif;color:red'>Server error.</h2>", 500

    return """
    <!DOCTYPE html>
    <html>
    <head><title>Verified — Narayan AI</title></head>
    <body style="margin:0;background:#0a0a0a;display:flex;align-items:center;justify-content:center;height:100vh;font-family:'Segoe UI',sans-serif;">
      <div style="text-align:center;background:#111;border:1px solid #c9a84c;border-radius:20px;padding:48px 56px;">
        <div style="font-size:48px;margin-bottom:16px;">✅</div>
        <div style="font-size:13px;letter-spacing:4px;color:#c9a84c;text-transform:uppercase;font-weight:700;margin-bottom:8px;">BTechX · Narayan AI</div>
        <h2 style="color:#f5d07a;margin:0 0 12px;">Email Verified!</h2>
        <p style="color:#888;margin:0 0 28px;">Your account is now active. You can log in.</p>
        <a href="/" style="background:linear-gradient(135deg,#c9a84c,#f5d07a);color:#000;font-weight:700;padding:12px 32px;border-radius:50px;text-decoration:none;font-size:14px;">
          Go to Login →
        </a>
      </div>
    </body>
    </html>
    """


# ── LOGIN ──────────────────────────────────────────────────

@auth_bp.route("/login", methods=["POST"])
def login():
    data     = request.json or {}
    email    = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400

    try:
        with get_db() as db:
            db.execute(
                f"SELECT id, full_name, email, password_hash, branch, roll_number, is_verified "
                f"FROM users WHERE email={PH}",
                (email,)
            )
            user = db.fetchone()
    except Exception as e:
        logger.error(f"Login DB error: {e}")
        return jsonify({"error": "Server error. Please try again."}), 500

    if not user:
        return jsonify({"error": "No account found with this email."}), 404

    u = dict(user)
    if u["password_hash"] != _hash(password):
        return jsonify({"error": "Incorrect password."}), 401

    if not u["is_verified"]:
        return jsonify({"error": "Please verify your email before logging in. Check your inbox."}), 403

    # Set session
    session["user_id"]    = u["id"]
    session["full_name"]  = u["full_name"]
    session["email"]      = u["email"]
    session["branch"]     = u["branch"]

    return jsonify({
        "message":    "Login successful!",
        "user": {
            "id":          u["id"],
            "full_name":   u["full_name"],
            "email":       u["email"],
            "branch":      u["branch"],
            "roll_number": u["roll_number"],
        }
    })


# ── LOGOUT ─────────────────────────────────────────────────

@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out successfully."})


# ── FORGOT PASSWORD ────────────────────────────────────────

@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    email = (request.json or {}).get("email", "").strip().lower()
    if not email:
        return jsonify({"error": "Email is required."}), 400

    token   = _token()
    expires = datetime.now() + timedelta(hours=1)

    try:
        with get_db() as db:
            db.execute(f"SELECT id, full_name FROM users WHERE email={PH}", (email,))
            user = db.fetchone()
            if not user:
                # Don't reveal if email exists
                return jsonify({"message": "If that email exists, a reset link has been sent."})
            u    = dict(user)
            db.execute(
                f"UPDATE users SET reset_token={PH}, reset_expires={PH} WHERE email={PH}",
                (token, expires.strftime("%Y-%m-%d %H:%M:%S"), email)
            )
    except Exception as e:
        logger.error(f"Forgot password error: {e}")
        return jsonify({"error": "Server error."}), 500

    try:
        from services.mail_service import send_reset_email
        send_reset_email(email, u["full_name"], token)
    except Exception as e:
        logger.warning(f"Reset email failed: {e}")

    return jsonify({"message": "If that email exists, a reset link has been sent."})


# ── RESET PASSWORD ─────────────────────────────────────────

@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    data     = request.json or {}
    token    = data.get("token", "").strip()
    password = data.get("password", "")

    if not token or not password:
        return jsonify({"error": "Token and new password are required."}), 400

    if not _valid_password(password):
        return jsonify({"error": "Password must be at least 8 characters."}), 400

    try:
        with get_db() as db:
            db.execute(
                f"SELECT id, reset_expires FROM users WHERE reset_token={PH}", (token,)
            )
            user = db.fetchone()
            if not user:
                return jsonify({"error": "Invalid or expired reset link."}), 400
            u = dict(user)
            if datetime.now() > datetime.strptime(str(u["reset_expires"]), "%Y-%m-%d %H:%M:%S"):
                return jsonify({"error": "Reset link has expired. Please request a new one."}), 400
            db.execute(
                f"UPDATE users SET password_hash={PH}, reset_token=NULL, reset_expires=NULL WHERE id={PH}",
                (_hash(password), u["id"])
            )
    except Exception as e:
        logger.error(f"Reset password error: {e}")
        return jsonify({"error": "Server error."}), 500

    return jsonify({"message": "Password reset successfully! You can now log in."})


# ── ME (get current user) ──────────────────────────────────

@auth_bp.route("/me", methods=["GET"])
def me():
    if not session.get("user_id"):
        return jsonify({"error": "Not logged in."}), 401
    return jsonify({
        "user_id":   session["user_id"],
        "full_name": session.get("full_name"),
        "email":     session.get("email"),
        "branch":    session.get("branch"),
    })
