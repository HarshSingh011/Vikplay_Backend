"""
Email utilities - SMTP relay on port 2525 (STARTTLS).
Port 2525 is not blocked by Render/cloud providers unlike 25/465/587.
Works with Brevo (smtp-relay.brevo.com), SendGrid (smtp.sendgrid.net),
Mailgun (smtp.mailgun.org), or any relay that supports port 2525.
"""
import ssl
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import os
import logging

logger = logging.getLogger(__name__)


class EmailUtils:
    """SMTP email sender via port 2525 relay (works on Render free tier)."""

    @property
    def smtp_server(self):
        return os.getenv("SMTP_SERVER", "smtp-relay.brevo.com")

    @property
    def smtp_port(self):
        return int(os.getenv("SMTP_PORT", "2525"))

    @property
    def sender_email(self):
        return os.getenv("EMAIL_USERNAME", "")

    @property
    def sender_password(self):
        return os.getenv("EMAIL_PASSWORD", "")

    @property
    def from_email(self):
        return os.getenv("FROM_EMAIL", self.sender_email)

    @property
    def sender_name(self):
        return os.getenv("SENDER_NAME", "VikPay")

    @property
    def dev_mode(self):
        return not (self.sender_email and self.sender_password)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _send_smtp(self, to_email: str, subject: str, body: str, html_body: str) -> bool:
        """Send via SMTP relay on port 2525 using STARTTLS."""
        host = self.smtp_server
        port = self.smtp_port
        logger.info(f"Sending email via {host}:{port} to {to_email}")
        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = f"{self.sender_name} <{self.from_email}>"
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))
            msg.attach(MIMEText(html_body, "html"))

            ctx = ssl.create_default_context()
            with smtplib.SMTP(host, port, timeout=30) as server:
                server.ehlo()
                server.starttls(context=ctx)
                server.ehlo()
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, to_email, msg.as_string())

            logger.info(f"Email sent successfully to {to_email}")
            return True
        except Exception as e:
            logger.error(f"SMTP failed ({host}:{port}): {e}")
            return False

    def _send_console(self, to_email: str, subject: str, body: str) -> bool:
        """Print email to console (no credentials set / dev mode)."""
        sep = "=" * 60
        print(f"\n{sep}\nEMAIL TO: {to_email}\nSUBJECT: {subject}\n{sep}\n{body}\n{sep}")
        logger.info(f"Email (console mode) for {to_email}")
        return True

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def send_email(self, to_email: str, subject: str, body: str, html_body: Optional[str] = None) -> bool:
        """Send email via SMTP relay, or log to console if no credentials."""
        html = html_body or f"<pre>{body}</pre>"
        if self.dev_mode:
            return self._send_console(to_email, subject, body)
        return self._send_smtp(to_email, subject, body, html)

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
