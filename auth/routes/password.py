"""
Password-related routes - forgot password, reset password
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from database import get_db
from auth.schemas import EmailVerify, OTPVerify, PasswordReset, MessageResponse
from auth.models import User, OTP
from auth.utils.email import email_utils
from auth.utils.otp import otp_utils
from auth.utils.password import password_utils
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

def send_reset_email_background(to_email: str, otp_code: str):
    """Send password reset OTP in background (non-blocking)"""
    try:
        email_utils.send_otp_email(to_email, otp_code, "password reset")
    except Exception as e:
        logger.error(f"Background password reset email failed for {to_email}: {e}")

@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(email_data: EmailVerify, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Send OTP for password reset
    """
    logger.info(f"Password reset request for email: {email_data.email}")
    try:
        # Check if user exists
        user = db.query(User).filter(User.email == email_data.email).first()
        if not user:
            logger.warning(f"Password reset attempted for non-existent email: {email_data.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User does not exist"
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
        otp_code = otp_utils.generate_otp(6)
        expires_at = datetime.utcnow() + timedelta(minutes=10)
        
        otp_record = OTP(
            email=email_data.email,
            otp_code=otp_code,
            otp_type="forgot_password",
            expires_at=expires_at
        )
        db.add(otp_record)
        db.commit()

        # Send OTP email in background (non-blocking)
        background_tasks.add_task(send_reset_email_background, email_data.email, otp_code)

        logger.info(f"Password reset OTP process completed for: {email_data.email}")
        return MessageResponse(
            message="If the email exists, you will receive a password reset OTP.",
            success=True
        )
        
    except HTTPException:
        raise
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
        user.hashed_password = password_utils.hash_password(reset_data.new_password)
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
