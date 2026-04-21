# ==========================================================
# 📧 NARYAN AI — MAIL SERVICE
#    Sends emails via Gmail SMTP (App Password)
# ==========================================================

import os
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text      import MIMEText

logger = logging.getLogger("NARYAN_AI.mail")

MAIL_EMAIL    = os.getenv("MAIL_EMAIL", "")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
APP_URL       = os.getenv("APP_URL", "http://127.0.0.1:5000")


def _send(to: str, subject: str, html: str):
    """Core SMTP send function."""
    if not MAIL_EMAIL or not MAIL_PASSWORD:
        logger.warning("Mail credentials not set — skipping email send.")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"Narayan AI — BTechX <{MAIL_EMAIL}>"
    msg["To"]      = to
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(MAIL_EMAIL, MAIL_PASSWORD)
            server.sendmail(MAIL_EMAIL, to, msg.as_string())
        logger.info(f"Email sent to {to}")
    except Exception as e:
        logger.error(f"Failed to send email to {to}: {e}")
        raise


def send_verification_email(to: str, name: str, token: str):
    link = f"{APP_URL}/api/auth/verify/{token}"
    html = f"""
    <!DOCTYPE html>
    <html>
    <body style="margin:0;padding:0;background:#0a0a0a;font-family:'Segoe UI',sans-serif;">
      <table width="100%" cellpadding="0" cellspacing="0" style="background:#0a0a0a;padding:40px 0;">
        <tr><td align="center">
          <table width="560" cellpadding="0" cellspacing="0" style="background:#111;border:1px solid #c9a84c;border-radius:16px;overflow:hidden;">
            <!-- Header -->
            <tr>
              <td style="background:linear-gradient(135deg,#c9a84c,#f5d07a);padding:32px;text-align:center;">
                <div style="font-size:13px;font-weight:700;letter-spacing:4px;color:#000;text-transform:uppercase;margin-bottom:8px;">⚡ BTechX</div>
                <div style="font-size:26px;font-weight:800;color:#000;">NARYAN AI</div>
                <div style="font-size:12px;color:#333;margin-top:4px;">Academic Intelligence Platform</div>
              </td>
            </tr>
            <!-- Body -->
            <tr>
              <td style="padding:36px 40px;">
                <p style="color:#f5d07a;font-size:18px;font-weight:700;margin:0 0 12px;">Hello, {name}! 👋</p>
                <p style="color:#aaa;font-size:14px;line-height:1.7;margin:0 0 28px;">
                  Welcome to <strong style="color:#f5d07a;">Narayan AI</strong> — your personal AI study assistant powered by BTechX.<br>
                  Please verify your college email to activate your account.
                </p>
                <div style="text-align:center;margin:28px 0;">
                  <a href="{link}" style="background:linear-gradient(135deg,#c9a84c,#f5d07a);color:#000;font-weight:700;font-size:15px;padding:14px 36px;border-radius:50px;text-decoration:none;display:inline-block;letter-spacing:0.5px;">
                    ✅ Verify My Email
                  </a>
                </div>
                <p style="color:#555;font-size:12px;text-align:center;margin-top:24px;">
                  Or copy this link: <span style="color:#c9a84c;">{link}</span>
                </p>
                <p style="color:#444;font-size:12px;text-align:center;margin-top:8px;">
                  This link expires in 24 hours.
                </p>
              </td>
            </tr>
            <!-- Footer -->
            <tr>
              <td style="background:#0a0a0a;padding:20px;text-align:center;border-top:1px solid #222;">
                <p style="color:#444;font-size:11px;margin:0;">
                  © 2024 BTechX · Narayan AI · CGU Odisha<br>
                  If you didn't register, ignore this email.
                </p>
              </td>
            </tr>
          </table>
        </td></tr>
      </table>
    </body>
    </html>
    """
    _send(to, "✅ Verify Your Narayan AI Account — BTechX", html)


def send_reset_email(to: str, name: str, token: str):
    link = f"{APP_URL}/reset-password?token={token}"
    html = f"""
    <!DOCTYPE html>
    <html>
    <body style="margin:0;padding:0;background:#0a0a0a;font-family:'Segoe UI',sans-serif;">
      <table width="100%" cellpadding="0" cellspacing="0" style="background:#0a0a0a;padding:40px 0;">
        <tr><td align="center">
          <table width="560" cellpadding="0" cellspacing="0" style="background:#111;border:1px solid #c9a84c;border-radius:16px;overflow:hidden;">
            <tr>
              <td style="background:linear-gradient(135deg,#c9a84c,#f5d07a);padding:32px;text-align:center;">
                <div style="font-size:13px;font-weight:700;letter-spacing:4px;color:#000;text-transform:uppercase;margin-bottom:8px;">⚡ BTechX</div>
                <div style="font-size:26px;font-weight:800;color:#000;">NARYAN AI</div>
                <div style="font-size:12px;color:#333;margin-top:4px;">Password Reset Request</div>
              </td>
            </tr>
            <tr>
              <td style="padding:36px 40px;">
                <p style="color:#f5d07a;font-size:18px;font-weight:700;margin:0 0 12px;">Hi {name},</p>
                <p style="color:#aaa;font-size:14px;line-height:1.7;margin:0 0 28px;">
                  We received a request to reset your <strong style="color:#f5d07a;">Narayan AI</strong> password.<br>
                  Click the button below to set a new password.
                </p>
                <div style="text-align:center;margin:28px 0;">
                  <a href="{link}" style="background:linear-gradient(135deg,#c9a84c,#f5d07a);color:#000;font-weight:700;font-size:15px;padding:14px 36px;border-radius:50px;text-decoration:none;display:inline-block;">
                    🔑 Reset My Password
                  </a>
                </div>
                <p style="color:#555;font-size:12px;text-align:center;margin-top:24px;">
                  This link expires in <strong style="color:#c9a84c;">1 hour</strong>.
                </p>
                <p style="color:#444;font-size:12px;text-align:center;margin-top:8px;">
                  If you didn't request this, you can safely ignore this email.
                </p>
              </td>
            </tr>
            <tr>
              <td style="background:#0a0a0a;padding:20px;text-align:center;border-top:1px solid #222;">
                <p style="color:#444;font-size:11px;margin:0;">
                  © 2024 BTechX · Narayan AI · CGU Odisha
                </p>
              </td>
            </tr>
          </table>
        </td></tr>
      </table>
    </body>
    </html>
    """
    _send(to, "🔑 Reset Your Narayan AI Password — BTechX", html)
