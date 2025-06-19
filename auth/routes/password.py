"""
Password-related routes - forgot password, reset password
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from auth.schemas import EmailVerify, OTPVerify, PasswordReset, MessageResponse
from auth.utils import UserUtils, OTPUtils, EmailUtils
import logging

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(email_data: EmailVerify, db: Session = Depends(get_db)):
    """
    Send OTP for password reset
    """
    try:
        # Check if user exists
        user = UserUtils.get_user_by_email(db, email_data.email)
        if not user:
            # For security, don't reveal if email exists or not
            return MessageResponse(
                message="If the email exists, you will receive a password reset OTP.",
                success=True
            )
        
        # Generate and send OTP
        otp = OTPUtils.create_otp(db, email_data.email, "forgot_password")
        email_sent = EmailUtils.send_password_reset_otp(email_data.email, otp)
        
        if not email_sent:
            logger.warning(f"Failed to send password reset OTP to {email_data.email}")
            # Don't fail the request if email fails, just log it
        
        logger.info(f"Password reset OTP sent to: {email_data.email}")
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
        is_valid = OTPUtils.verify_otp(db, otp_data.email, otp_data.otp, "forgot_password")
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired OTP"
            )
        
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
    Reset password after OTP verification
    """
    try:
        # Verify OTP first
        is_valid = OTPUtils.verify_otp(db, reset_data.email, reset_data.otp, "forgot_password")
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired OTP"
            )
        
        # Update password
        password_updated = UserUtils.update_user_password(db, reset_data.email, reset_data.new_password)
        
        if not password_updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
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
