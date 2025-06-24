"""
Password-related routes - forgot password, reset password
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from auth.schemas import EmailVerify, OTPVerify, PasswordReset, MessageResponse
from auth.models import User, OTP
import bcrypt
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import os
import logging
from dotenv import load_dotenv

# Load environment variables - force override
load_dotenv(override=True)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Email configuration
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
EMAIL_USERNAME = os.getenv("EMAIL_USERNAME", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", EMAIL_USERNAME)

def generate_otp() -> str:
    """Generate 6-digit OTP"""
    return ''.join([str(secrets.randbelow(10)) for _ in range(6)])

def send_email(to_email: str, subject: str, body: str) -> bool:
    """Send email via SMTP"""
    try:
        if not EMAIL_USERNAME or not EMAIL_PASSWORD:
            logger.info(f"EMAIL CONSOLE MODE - To: {to_email}, Subject: {subject}")
            return True
            
        msg = MIMEMultipart()
        msg['From'] = FROM_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
        server.sendmail(FROM_EMAIL, to_email, msg.as_string())
        server.quit()
        
        logger.info(f"Email sent successfully to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {str(e)}")
        return False

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(email_data: EmailVerify, db: Session = Depends(get_db)):
    """
    Send OTP for password reset
    """
    logger.info(f"Password reset request for email: {email_data.email}")
    try:
        # Check if user exists
        user = db.query(User).filter(User.email == email_data.email).first()
        if not user:
            # For security, return generic message but log the attempt
            logger.warning(f"Password reset attempted for non-existent email: {email_data.email}")
            return MessageResponse(
                message="If the email exists, you will receive a password reset OTP.",
                success=True
            )
        
        # Clean up any existing OTP for this email and type
        existing_otps = db.query(OTP).filter(
            OTP.email == email_data.email,
            OTP.otp_type == "forgot_password"
        ).all()
        for otp in existing_otps:
            db.delete(otp)
        db.commit()
        
        # Generate and store OTP
        otp_code = generate_otp()
        expires_at = datetime.utcnow() + timedelta(minutes=10)  # 10 minute expiry
        
        otp_record = OTP(
            email=email_data.email,
            otp_code=otp_code,
            otp_type="forgot_password",
            expires_at=expires_at
        )
        db.add(otp_record)
        db.commit()
        
        # Send OTP email
        subject = "VikPay - Password Reset OTP"
        body = f"""
        <html>
        <body>
            <h2>Password Reset Request</h2>
            <p>You have requested to reset your password for your VikPay account.</p>
            <p>Please use the following OTP to reset your password:</p>
            <div style="background-color: #f0f0f0; padding: 20px; text-align: center; margin: 20px 0;">
                <h3 style="color: #007bff; font-size: 24px; letter-spacing: 5px;">{otp_code}</h3>
            </div>
            <p>This OTP will expire in 10 minutes.</p>
            <p>If you did not request a password reset, please ignore this email.</p>
            <br>
            <p>Best regards,<br>VikPay Team</p>
        </body>
        </html>
        """
        email_sent = send_email(email_data.email, subject, body)
        
        if not email_sent:
            logger.warning(f"Failed to send password reset OTP to {email_data.email}")
            # Don't fail the request for security reasons, just log it
        
        logger.info(f"Password reset OTP process completed for: {email_data.email}")
        return MessageResponse(
            message="If the email exists, you will receive a password reset OTP.",
            success=True
        )
        
    except Exception as e:
        logger.error(f"Forgot password error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process password reset request. Please try again."
        )

@router.post("/verify-forgot-password-otp", response_model=MessageResponse)
async def verify_forgot_password_otp(otp_data: OTPVerify, db: Session = Depends(get_db)):
    """
    Verify OTP for password reset
    """
    try:
        # Verify OTP
        otp_record = db.query(OTP).filter(
            OTP.email == otp_data.email,
            OTP.otp_code == otp_data.otp,
            OTP.otp_type == "forgot_password",
            OTP.is_used == False,
            OTP.expires_at > datetime.utcnow()
        ).first()
        
        if not otp_record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired OTP"
            )
        
        # Mark OTP as used
        otp_record.is_used = True
        db.commit()
        
        logger.info(f"Password reset OTP verified for: {otp_data.email}")
        return MessageResponse(
            message="OTP verified successfully! You can now reset your password.",
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OTP verification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OTP verification failed. Please try again."
        )

@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(reset_data: PasswordReset, db: Session = Depends(get_db)):
    """
    Reset password directly without OTP verification
    """
    logger.info(f"Password reset request for email: {reset_data.email}")
    try:
        # Get user
        user = db.query(User).filter(User.email == reset_data.email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User with this email does not exist"
            )
        
        # Update password
        user.hashed_password = hash_password(reset_data.new_password)
        db.commit()
        
        logger.info(f"Password reset successfully for: {reset_data.email}")
        return MessageResponse(
            message="Password reset successfully! You can now login with your new password.",
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed. Please try again."
        )
