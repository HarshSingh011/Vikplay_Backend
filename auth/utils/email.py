"""
Email utilities - HTTP API (no SMTP needed, works on Render free tier).

Primary:  Brevo    -> set BREVO_API_KEY  (300 emails/day free, sends to ANYONE)
Fallback: Resend   -> set RESEND_API_KEY  (3000/mo free, needs domain verification)
Console:  neither set -> prints to logs

Brevo: https://brevo.com  (former Sendinblue)
  - Sign up free, go to SMTP & API -> API Keys -> Generate
  - Just verify your FROM_EMAIL sender address (not a domain)
  - Can send to ANY recipient immediately
"""
import requests
from typing import Optional
import os
import logging

logger = logging.getLogger(__name__)

# Startup diagnostic
_brevo = os.getenv("BREVO_API_KEY", "").strip()
_resend = os.getenv("RESEND_API_KEY", "").strip()
if _brevo:
    print(f"[EMAIL] Brevo API key detected: {_brevo[:8]}... (len={len(_brevo)})")
elif _resend:
    print(f"[EMAIL] Resend API key detected: {_resend[:8]}... (len={len(_resend)})")
else:
    print("[EMAIL] WARNING: No BREVO_API_KEY or RESEND_API_KEY found! Emails will only log to console.")


class EmailUtils:
    """HTTP-based email sender. Brevo -> Resend -> console."""

    @property
    def brevo_api_key(self):
        return os.getenv("BREVO_API_KEY", "").strip()

    @property
    def resend_api_key(self):
        return os.getenv("RESEND_API_KEY", "").strip()

    @property
    def from_email(self):
        return os.getenv("FROM_EMAIL", "").strip()

    @property
    def sender_name(self):
        return os.getenv("SENDER_NAME", "VikPay").strip()

    # ------------------------------------------------------------------
    # Internal senders
    # ------------------------------------------------------------------

    def _send_brevo(self, to_email: str, subject: str, html_body: str, text_body: str) -> bool:
        """
        Send via Brevo (Sendinblue) HTTP API.
        300 emails/day free. Sends to ANY recipient.
        Only requires verifying your sender email address (not a domain).
        Docs: https://developers.brevo.com/reference/sendtransacemail
        """
        try:
            resp = requests.post(
                "https://api.brevo.com/v3/smtp/email",
                headers={
                    "api-key": self.brevo_api_key,
                    "Content-Type": "application/json",
                    "accept": "application/json",
                },
                json={
                    "sender": {"name": self.sender_name, "email": self.from_email},
                    "to": [{"email": to_email}],
                    "subject": subject,
                    "htmlContent": html_body,
                    "textContent": text_body,
                },
                timeout=15,
            )
            if resp.status_code in (200, 201):
                logger.info(f"Email sent via Brevo to {to_email}")
                return True
            logger.error(f"Brevo error {resp.status_code}: {resp.text}")
            return False
        except Exception as e:
            logger.error(f"Brevo request failed: {e}")
            return False

    def _send_resend(self, to_email: str, subject: str, html_body: str, text_body: str) -> bool:
        """Send via Resend REST API (needs domain verification to send to others)."""
        from_addr = f"{self.sender_name} <{self.from_email or 'onboarding@resend.dev'}>"
        try:
            resp = requests.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {self.resend_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "from": from_addr,
                    "to": [to_email],
                    "subject": subject,
                    "html": html_body,
                    "text": text_body,
                },
                timeout=15,
            )
            if resp.status_code in (200, 201):
                logger.info(f"Email sent via Resend to {to_email}")
                return True
            logger.error(f"Resend error {resp.status_code}: {resp.text}")
            return False
        except Exception as e:
            logger.error(f"Resend request failed: {e}")
            return False

    def _send_console(self, to_email: str, subject: str, body: str) -> bool:
        """Print email to logs (dev/test mode)."""
        sep = "=" * 60
        print(f"\n{sep}\nEMAIL TO: {to_email}\nSUBJECT: {subject}\n{sep}\n{body}\n{sep}")
        logger.info(f"Email (console/dev mode) logged for {to_email}")
        return True

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def send_email(self, to_email: str, subject: str, body: str, html_body: Optional[str] = None) -> bool:
        """Send email. Tries Brevo -> Resend -> console."""
        html = html_body or f"<pre>{body}</pre>"
        if self.brevo_api_key:
            return self._send_brevo(to_email, subject, html, body)
        if self.resend_api_key:
            return self._send_resend(to_email, subject, html, body)
        return self._send_console(to_email, subject, body)

    def send_otp_email(self, to_email: str, otp: str, purpose: str = "verification") -> bool:
        """Send OTP email."""
        subject = f"Your {purpose.title()} Code - VikPay"
        body = (
            f"Hello,\n\nYour {purpose} code is: {otp}\n\n"
            f"This code expires in 15 minutes. Do not share it.\n\nVikPay Team"
        )
        html_body = f"""<html><body style="font-family:Arial,sans-serif;color:#333">
  <div style="max-width:520px;margin:0 auto;padding:20px">
    <h1 style="color:#007bff">VikPay</h1>
    <h2>Your {purpose.title()} Code</h2>
    <div style="background:#f8f9fa;border:2px solid #007bff;border-radius:8px;
                padding:20px;text-align:center;margin:20px 0">
      <h1 style="margin:0;color:#007bff;font-size:36px;letter-spacing:10px">{otp}</h1>
    </div>
    <p>Expires in <strong>15 minutes</strong>. Do not share.</p>
    <hr/><p>VikPay Team</p>
  </div></body></html>"""
        return self.send_email(to_email, subject, body, html_body)

    def send_welcome_email(self, to_email: str, username: str) -> bool:
        """Send welcome email."""
        subject = "Welcome to VikPay!"
        body = f"Hello {username},\n\nYour account is active and verified.\n\nVikPay Team"
        html_body = f"""<html><body style="font-family:Arial,sans-serif;color:#333">
  <div style="max-width:520px;margin:0 auto;padding:20px">
    <h1 style="color:#007bff">VikPay</h1>
    <h2>Welcome, {username}!</h2>
    <p>Your account has been created and verified.</p>
    <hr/><p>VikPay Team</p>
  </div></body></html>"""
        return self.send_email(to_email, subject, body, html_body)

    def send_password_reset_confirmation(self, to_email: str, username: str) -> bool:
        """Send password reset confirmation."""
        subject = "Password Reset Successful - VikPay"
        body = f"Hello {username},\n\nYour password was reset. If not you, contact support.\n\nVikPay Team"
        html_body = f"""<html><body style="font-family:Arial,sans-serif;color:#333">
  <div style="max-width:520px;margin:0 auto;padding:20px">
    <h1 style="color:#007bff">VikPay</h1>
    <h2>Password Reset Successful</h2>
    <p>Hello {username}, your password was reset successfully.</p>
    <p style="color:#c00"><strong>If this wasn\'t you, contact support immediately.</strong></p>
    <hr/><p>VikPay Team</p>
  </div></body></html>"""
        return self.send_email(to_email, subject, body, html_body)


# Global singleton
email_utils = EmailUtils()
