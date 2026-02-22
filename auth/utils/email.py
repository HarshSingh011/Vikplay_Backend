"""
Email utilities - pure SMTP, works with Gmail on port 465 (SSL) or 587 (STARTTLS).
Forces IPv4 to avoid "Network is unreachable" errors on Render (IPv6 not routed).
"""
import ssl
import socket
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import os
import logging

logger = logging.getLogger(__name__)


class EmailUtils:
    """SMTP email sender with IPv4 forcing and SSL/STARTTLS auto-selection."""

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

    def _connect_ipv4(self, host: str, port: int, timeout: int = 30):
        """
        Create a TCP socket that is forcibly connected over IPv4.
        Returns (raw_socket, ipv4_addr_used).
        Avoids 'Network is unreachable' / timeout caused by IPv6 being
        tried first on Render containers where IPv6 routes don't exist.
        """
        # getaddrinfo with AF_INET returns only IPv4 results
        infos = socket.getaddrinfo(host, port, socket.AF_INET, socket.SOCK_STREAM)
        if not infos:
            raise OSError(f"No IPv4 address found for {host}")
        ipv4_addr = infos[0][4][0]
        logger.info(f"Resolved {host} → {ipv4_addr} (IPv4)")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((ipv4_addr, port))
        return sock, ipv4_addr

    def _send_smtp(self, to_email: str, subject: str, body: str, html_body: str) -> bool:
        """
        Send via SMTP using an explicitly IPv4-connected socket.
        Port 465 → SMTP_SSL (implicit TLS).
        Port 587 → SMTP + STARTTLS.
        The TLS cert is always validated against the real hostname.
        """
        host = self.smtp_server
        port = self.smtp_port
        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = f"{self.sender_name} <{self.from_email}>"
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))
            msg.attach(MIMEText(html_body, "html"))

            logger.info(f"Connecting to {host}:{port} over IPv4 ...")
            raw_sock, ipv4 = self._connect_ipv4(host, port)

            ctx = ssl.create_default_context()

            if port == 465:
                # Wrap the pre-connected IPv4 socket in TLS.
                # server_hostname=host ensures cert is verified against smtp.gmail.com.
                ssl_sock = ctx.wrap_socket(raw_sock, server_hostname=host)
                server = smtplib.SMTP()
                server.sock = ssl_sock
                server.file = ssl_sock.makefile("rb")
                server._host = host
                # Read the 220 greeting the server sends on connect
                code, msg = server.getreply()
                if code != 220:
                    raise smtplib.SMTPConnectError(code, msg)
                server.ehlo(host)
            else:
                # STARTTLS over plain TCP first
                server = smtplib.SMTP()
                server.sock = raw_sock
                server.file = raw_sock.makefile("rb")
                server._host = host
                # Read the 220 greeting
                code, msg = server.getreply()
                if code != 220:
                    raise smtplib.SMTPConnectError(code, msg)
                server.ehlo(host)
                server.starttls(context=ctx)
                server.ehlo(host)

            server.login(self.sender_email, self.sender_password)
            server.sendmail(self.sender_email, to_email, msg.as_string())
            server.quit()
            logger.info(f"Email sent to {to_email} via {ipv4}:{port}")
            return True
        except Exception as e:
            logger.error(f"SMTP failed ({host}:{port}): {e}")
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
