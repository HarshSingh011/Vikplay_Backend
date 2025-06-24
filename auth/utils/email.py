"""
Email utilities for sending emails
"""
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import os
import logging
from dotenv import load_dotenv

# Force load .env file to override system environment variables
load_dotenv(override=True)

logger = logging.getLogger(__name__)


class EmailUtils:
    """Utility class for email operations"""
    
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.sender_email = os.getenv("EMAIL_USERNAME", "")
        self.sender_password = os.getenv("EMAIL_PASSWORD", "")
        self.from_email = os.getenv("FROM_EMAIL", self.sender_email)
        self.sender_name = os.getenv("SENDER_NAME", "VikPay")
        
        # Development mode - if no email credentials, use console logging
        self.dev_mode = not (self.sender_email and self.sender_password)
        
        if self.dev_mode:
            logger.info("📧 Email service running in DEVELOPMENT MODE - emails will be logged to console")
    
    def _send_email_console(self, to_email: str, subject: str, body: str) -> bool:
        """Log email to console instead of sending (development mode)"""
        print("\n" + "="*60)
        print("📧 EMAIL (Development Mode)")
        print("="*60)
        print(f"From: {self.from_email}")
        print(f"To: {to_email}")
        print(f"Subject: {subject}")
        print("-"*60)
        print(body)
        print("="*60)
        logger.info(f"Email logged to console for {to_email}")
        return True
    
    def _create_connection(self) -> Optional[smtplib.SMTP]:
        """Create SMTP connection"""
        try:
            # Create SMTP session
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()  # Enable security
            server.login(self.sender_email, self.sender_password)
            return server
        except Exception as e:
            logger.error(f"Failed to create SMTP connection: {e}")
            return None
    
    def send_email(self, to_email: str, subject: str, body: str, html_body: Optional[str] = None) -> bool:
        """Send an email"""
        # If in development mode, log to console
        if self.dev_mode:
            email_content = html_body if html_body else body
            return self._send_email_console(to_email, subject, email_content)
        
        try:
            # Create message container
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.sender_name} <{self.from_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add plain text part
            text_part = MIMEText(body, 'plain')
            msg.attach(text_part)
            
            # Add HTML part if provided
            if html_body:
                html_part = MIMEText(html_body, 'html')
                msg.attach(html_part)
            
            # Create connection and send email
            server = self._create_connection()
            if not server:
                return False
            
            text = msg.as_string()
            server.sendmail(self.sender_email, to_email, text)
            server.quit()
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
    
    def send_otp_email(self, to_email: str, otp: str, purpose: str = "verification") -> bool:
        """Send OTP via email"""
        subject = f"Your {purpose.title()} Code - VikPay"
        
        # Plain text body
        body = f"""
Hello,

Your {purpose} code is: {otp}

This code will expire in 15 minutes. Please do not share this code with anyone.

If you didn't request this code, please ignore this email.

Best regards,
VikPay Team
        """.strip()
        
        # HTML body
        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="text-align: center; margin-bottom: 30px;">
                        <h1 style="color: #007bff;">VikPay</h1>
                    </div>
                    
                    <h2>Your {purpose.title()} Code</h2>
                    
                    <p>Hello,</p>
                    
                    <p>Your {purpose} code is:</p>
                    
                    <div style="background-color: #f8f9fa; border: 2px solid #007bff; border-radius: 8px; padding: 20px; text-align: center; margin: 20px 0;">
                        <h1 style="margin: 0; color: #007bff; font-size: 32px; letter-spacing: 8px;">{otp}</h1>
                    </div>
                    
                    <p><strong>Important:</strong></p>
                    <ul>
                        <li>This code will expire in 15 minutes</li>
                        <li>Please do not share this code with anyone</li>
                        <li>If you didn't request this code, please ignore this email</li>
                    </ul>
                    
                    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; text-align: center; color: #666;">
                        <p>Best regards,<br>VikPay Team</p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        return self.send_email(to_email, subject, body, html_body)
    
    def send_welcome_email(self, to_email: str, username: str) -> bool:
        """Send welcome email after successful registration"""
        subject = "Welcome to VikPay!"
        
        body = f"""
Hello {username},

Welcome to VikPay! Your account has been successfully created and verified.

You can now start using all the features of our platform.

If you have any questions, feel free to contact our support team.

Best regards,
VikPay Team
        """.strip()
        
        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="text-align: center; margin-bottom: 30px;">
                        <h1 style="color: #007bff;">VikPay</h1>
                    </div>
                    
                    <h2>Welcome to VikPay!</h2>
                    
                    <p>Hello {username},</p>
                    
                    <p>Welcome to VikPay! Your account has been successfully created and verified.</p>
                    
                    <div style="background-color: #d4edda; border: 1px solid #c3e6cb; border-radius: 8px; padding: 20px; margin: 20px 0;">
                        <p style="margin: 0;"><strong>✅ Account Status:</strong> Active and Verified</p>
                    </div>
                    
                    <p>You can now start using all the features of our platform:</p>
                    <ul>
                        <li>Video streaming and uploads</li>
                        <li>Live broadcasting</li>
                        <li>WebRTC streaming</li>
                        <li>And much more!</li>
                    </ul>
                    
                    <p>If you have any questions, feel free to contact our support team.</p>
                    
                    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; text-align: center; color: #666;">
                        <p>Best regards,<br>VikPay Team</p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        return self.send_email(to_email, subject, body, html_body)
    
    def send_password_reset_confirmation(self, to_email: str, username: str) -> bool:
        """Send password reset confirmation email"""
        subject = "Password Reset Successful - VikPay"
        
        body = f"""
Hello {username},

Your password has been successfully reset.

If you didn't make this change, please contact our support team immediately.

Best regards,
VikPay Team
        """.strip()
        
        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="text-align: center; margin-bottom: 30px;">
                        <h1 style="color: #007bff;">VikPay</h1>
                    </div>
                    
                    <h2>Password Reset Successful</h2>
                    
                    <p>Hello {username},</p>
                    
                    <div style="background-color: #d4edda; border: 1px solid #c3e6cb; border-radius: 8px; padding: 20px; margin: 20px 0;">
                        <p style="margin: 0;"><strong>✅ Your password has been successfully reset.</strong></p>
                    </div>
                    
                    <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 8px; padding: 15px; margin: 20px 0;">
                        <p style="margin: 0;"><strong>⚠️ Security Notice:</strong> If you didn't make this change, please contact our support team immediately.</p>
                    </div>
                    
                    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; text-align: center; color: #666;">
                        <p>Best regards,<br>VikPay Team</p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        return self.send_email(to_email, subject, body, html_body)


# Global instance
email_utils = EmailUtils()
