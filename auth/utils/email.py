"""
Email utilities - SMTP with automatic IPv6/IPv4 fallback and port fallback.
Tries every combination: (IPv6, port 465) → (IPv6, port 587) →
                         (IPv4, port 465) → (IPv4, port 587)
Uses standard smtplib with the real hostname so TLS cert validation works correctly.
"""
import ssl
import socket
import smtplib
from contextlib import contextmanager
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import os
import logging

logger = logging.getLogger(__name__)


@contextmanager
def _force_addr_family(family: int):
    """
    Context manager: temporarily patches socket.getaddrinfo so it only
    returns addresses of the given family (AF_INET6 or AF_INET).
    smtplib uses getaddrinfo internally, so patching it here makes SMTP_SSL
    connect over the desired protocol while still using the real hostname for
    TLS SNI / certificate validation.
    """
    original = socket.getaddrinfo

    def patched(host, port, fam=0, type=0, proto=0, flags=0):
        return original(host, port, family, type, proto, flags)

    socket.getaddrinfo = patched
    try:
        yield
    finally:
        socket.getaddrinfo = original


class EmailUtils:
    """SMTP email sender - auto-selects IPv6/IPv4 and SSL/STARTTLS."""

    def __init__(self):
        self.sender_name = os.getenv("SENDER_NAME", "VikPay")

    @property
    def smtp_server(self):
        return os.getenv("SMTP_SERVER", "smtp.gmail.com")

    @property
    def smtp_port(self):
        return int(os.getenv("SMTP_PORT", "465"))

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
    def dev_mode(self):
        return not (self.sender_email and self.sender_password)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _try_connect(self, host: str, port: int, family: int) -> Optional[smtplib.SMTP]:
        """
        Attempt one SMTP connection using the given address family and port.
        Returns a logged-in SMTP server object, or None on failure.
        Port 465 → SMTP_SSL (immediate TLS).
        Port 587 → SMTP + STARTTLS.
        """
        family_name = "IPv6" if family == socket.AF_INET6 else "IPv4"
        mode = "SSL" if port == 465 else "STARTTLS"
        logger.info(f"Trying {host}:{port} via {family_name} ({mode}) ...")
        try:
            ctx = ssl.create_default_context()
            with _force_addr_family(family):
                if port == 465:
                    server = smtplib.SMTP_SSL(host, port, context=ctx, timeout=20)
                else:
                    server = smtplib.SMTP(host, port, timeout=20)
                    server.ehlo()
                    server.starttls(context=ctx)
                    server.ehlo()
            server.login(self.sender_email, self.sender_password)
            logger.info(f"Connected via {family_name}:{port}")
            return server
        except Exception as e:
            logger.warning(f"  {family_name}:{port} failed — {e}")
            return None

    def _send_smtp(self, to_email: str, subject: str, body: str, html_body: str) -> bool:
        """
        Build message, then try every combination until one succeeds:
          1. IPv6 + configured port
          2. IPv4 + configured port
          3. IPv6 + alternate port (465↔587)
          4. IPv4 + alternate port
        """
        host = self.smtp_server
        port = self.smtp_port
        alt_port = 587 if port == 465 else 465

        attempts = [
            (socket.AF_INET6, port),
            (socket.AF_INET,  port),
            (socket.AF_INET6, alt_port),
            (socket.AF_INET,  alt_port),
        ]

        msg = MIMEMultipart("alternative")
        msg["From"] = f"{self.sender_name} <{self.from_email}>"
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        for family, p in attempts:
            server = self._try_connect(host, p, family)
            if server:
                try:
                    server.sendmail(self.sender_email, to_email, msg.as_string())
                    server.quit()
                    logger.info(f"Email sent to {to_email}")
                    return True
                except Exception as e:
                    logger.warning(f"Send failed after connect: {e}")
                    try:
                        server.quit()
                    except Exception:
                        pass

        logger.error(f"All SMTP attempts failed for {to_email}")
        return False

    def _send_console(self, to_email: str, subject: str, body: str) -> bool:
        """Print email to console (development/testing mode)."""
        sep = "=" * 60
        dash = "-" * 60
        print(f"\n{sep}\nEMAIL TO: {to_email}\nSUBJECT: {subject}\n{dash}\n{body}\n{sep}")
        logger.info(f"Email logged to console for {to_email}")
        return True

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def send_email(self, to_email: str, subject: str, body: str, html_body: Optional[str] = None) -> bool:
        """Send email — uses SMTP if credentials set, otherwise logs to console."""
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
    <p>Your code:</p>
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
    <p style="color:#c00"><strong>If this wasn't you, contact support immediately.</strong></p>
    <hr/><p>VikPay Team</p>
  </div></body></html>"""
        return self.send_email(to_email, subject, body, html_body)


# Global singleton
email_utils = EmailUtils()
