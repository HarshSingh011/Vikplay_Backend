"""
Email utilities - HTTP API (no SMTP, works on Render free tier).

Primary:  Resend   → set RESEND_API_KEY
Fallback: SendGrid → set SENDGRID_API_KEY
Console:  neither key set → prints to logs (dev/test mode)

Resend free tier:  3,000 emails/month  https://resend.com
SendGrid free tier: 100 emails/day     https://sendgrid.com
"""
import requests
from typing import Optional
import os
import logging

logger = logging.getLogger(__name__)


class EmailUtils:
    """HTTP-based email sender. Uses Resend, then SendGrid, then console."""

    @property
    def resend_api_key(self):
        return os.getenv("RESEND_API_KEY", "")

    @property
    def sendgrid_api_key(self):
        return os.getenv("SENDGRID_API_KEY", "")

    @property
    def from_email(self):
        return os.getenv("FROM_EMAIL", "")

    @property
    def sender_name(self):
        return os.getenv("SENDER_NAME", "VikPay")

    @property
    def dev_mode(self):
        return not (self.resend_api_key or self.sendgrid_api_key)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _send_resend(self, to_email: str, subject: str, html_body: str, text_body: str) -> bool:
        """Send via Resend REST API (https://resend.com)."""
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

    def _send_sendgrid(self, to_email: str, subject: str, html_body: str, text_body: str) -> bool:
        """Send via SendGrid REST API (https://sendgrid.com)."""
        from_addr = self.from_email or "noreply@example.com"
        try:
            resp = requests.post(
                "https://api.sendgrid.com/v3/mail/send",
                headers={
                    "Authorization": f"Bearer {self.sendgrid_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "personalizations": [{"to": [{"email": to_email}]}],
                    "from": {"email": from_addr, "name": self.sender_name},
                    "subject": subject,
                    "content": [
                        {"type": "text/plain", "value": text_body},
                        {"type": "text/html", "value": html_body},
                    ],
                },
                timeout=15,
            )
            if resp.status_code == 202:
                logger.info(f"Email sent via SendGrid to {to_email}")
                return True
            logger.error(f"SendGrid error {resp.status_code}: {resp.text}")
            return False
        except Exception as e:
            logger.error(f"SendGrid request failed: {e}")
            return False

    def _send_console(self, to_email: str, subject: str, body: str) -> bool:
        """Print email to logs when no API key is configured."""
        sep = "=" * 60
        print(f"\n{sep}\nEMAIL TO: {to_email}\nSUBJECT: {subject}\n{sep}\n{body}\n{sep}")
        logger.info(f"Email (console/dev mode) logged for {to_email}")
        return True

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def send_email(self, to_email: str, subject: str, body: str, html_body: Optional[str] = None) -> bool:
        """Send email. Tries Resend → SendGrid → console."""
        html = html_body or f"<pre>{body}</pre>"

        if self.resend_api_key:
            return self._send_resend(to_email, subject, html, body)

        if self.sendgrid_api_key:
            return self._send_sendgrid(to_email, subject, html, body)

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
        """Send welcome email after successful registration."""
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
