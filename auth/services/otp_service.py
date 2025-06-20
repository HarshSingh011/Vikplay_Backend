"""
OTP service for managing one-time passwords
"""
from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from auth.services.base import BaseService, ServiceResult, ValidationError, RateLimitError
from auth.repositories import otp_repository, user_repository
from auth.utils import otp_utils, email_utils


class OTPService(BaseService):
    """Service for OTP-related operations"""
    
    def __init__(self, db: Session):
        super().__init__(db)
        self.otp_repo = otp_repository
        self.user_repo = user_repository
    
    def send_verification_otp(self, email: str) -> ServiceResult:
        """Send OTP for email verification"""
        try:
            # Check rate limiting
            if not self.otp_repo.can_request_new_otp(self.db, email, "verification", cooldown_minutes=1):
                return ServiceResult.error_result("Please wait before requesting another OTP")
            
            # Generate OTP
            otp_code, expires_at = otp_utils.create_otp_with_expiry(length=6, expiry_minutes=15)
            
            # Store OTP in database
            self.otp_repo.create_otp(
                self.db,
                email=email,
                otp_code=otp_code,
                purpose="verification",
                expires_at=expires_at
            )
            
            # Send OTP via email
            email_sent = email_utils.send_otp_email(email, otp_code, "verification")
            
            if not email_sent:
                return ServiceResult.error_result("Failed to send OTP email")
            
            return ServiceResult.success_result(
                data={
                    "email": email,
                    "expires_in_minutes": 15
                },
                message="OTP sent successfully"
            )
            
        except Exception as e:
            return ServiceResult.error_result(f"Failed to send OTP: {str(e)}")
    
    def verify_email_otp(self, email: str, otp_code: str) -> ServiceResult:
        """Verify OTP for email verification"""
        try:
            # Validate OTP format
            if not otp_utils.validate_otp_format(otp_code, 6):
                return ServiceResult.error_result("Invalid OTP format")
            
            # Get valid OTP
            otp = self.otp_repo.get_valid_otp(self.db, email, otp_code, "verification")
            if not otp:
                return ServiceResult.error_result("Invalid or expired OTP")
            
            # Mark OTP as used
            self.otp_repo.mark_otp_as_used(self.db, otp)
            
            # Get user and activate if exists
            user = self.user_repo.get_by_email(self.db, email)
            if user and not user.is_active:
                self.user_repo.activate_user(self.db, user)
                
                # Send welcome email
                email_utils.send_welcome_email(user.email, user.username)
                
                return ServiceResult.success_result(
                    data={
                        "email": email,
                        "user_activated": True
                    },
                    message="Email verified and account activated successfully"
                )
            
            return ServiceResult.success_result(
                data={
                    "email": email,
                    "user_activated": False
                },
                message="Email verified successfully"
            )
            
        except Exception as e:
            return ServiceResult.error_result(f"OTP verification failed: {str(e)}")
    
    def send_password_reset_otp(self, email: str) -> ServiceResult:
        """Send OTP for password reset"""
        try:
            # Check if user exists
            user = self.user_repo.get_by_email(self.db, email)
            if not user:
                return ServiceResult.error_result("Email not found")
            
            # Check rate limiting
            if not self.otp_repo.can_request_new_otp(self.db, email, "password_reset", cooldown_minutes=2):
                return ServiceResult.error_result("Please wait before requesting another OTP")
            
            # Invalidate previous OTPs
            self.otp_repo.invalidate_user_otps(self.db, email, "password_reset")
            
            # Generate OTP
            otp_code, expires_at = otp_utils.create_otp_with_expiry(length=6, expiry_minutes=15)
            
            # Store OTP in database
            self.otp_repo.create_otp(
                self.db,
                email=email,
                otp_code=otp_code,
                purpose="password_reset",
                expires_at=expires_at
            )
            
            # Send OTP via email
            email_sent = email_utils.send_otp_email(email, otp_code, "password reset")
            
            if not email_sent:
                return ServiceResult.error_result("Failed to send OTP email")
            
            return ServiceResult.success_result(
                data={
                    "email": email,
                    "expires_in_minutes": 15
                },
                message="Password reset OTP sent successfully"
            )
            
        except Exception as e:
            return ServiceResult.error_result(f"Failed to send password reset OTP: {str(e)}")
    
    def verify_password_reset_otp(self, email: str, otp_code: str) -> ServiceResult:
        """Verify OTP for password reset"""
        try:
            # Validate OTP format
            if not otp_utils.validate_otp_format(otp_code, 6):
                return ServiceResult.error_result("Invalid OTP format")
            
            # Check if user exists
            user = self.user_repo.get_by_email(self.db, email)
            if not user:
                return ServiceResult.error_result("Email not found")
            
            # Get valid OTP
            otp = self.otp_repo.get_valid_otp(self.db, email, otp_code, "password_reset")
            if not otp:
                return ServiceResult.error_result("Invalid or expired OTP")
            
            # Mark OTP as used
            self.otp_repo.mark_otp_as_used(self.db, otp)
            
            return ServiceResult.success_result(
                data={
                    "email": email,
                    "otp_verified": True
                },
                message="OTP verified successfully. You can now reset your password."
            )
            
        except Exception as e:
            return ServiceResult.error_result(f"OTP verification failed: {str(e)}")
    
    def verify_otp(self, email: str, otp_code: str, otp_type: str) -> ServiceResult:
        """Verify OTP for different types (registration, forgot_password)"""
        try:
            if otp_type == "registration":
                return self.verify_email_otp(email, otp_code)
            elif otp_type == "forgot_password":
                return self.verify_password_reset_otp(email, otp_code)
            else:
                return ServiceResult.error_result("Invalid OTP type")
        except Exception as e:
            return ServiceResult.error_result(f"OTP verification failed: {str(e)}")
    
    def cleanup_expired_otps(self) -> ServiceResult:
        """Clean up expired OTPs (for maintenance)"""
        try:
            count = self.otp_repo.cleanup_expired_otps(self.db)
            return ServiceResult.success_result(
                data={"cleaned_count": count},
                message=f"Cleaned up {count} expired OTPs"
            )
        except Exception as e:
            return ServiceResult.error_result(f"Cleanup failed: {str(e)}")


def get_otp_service(db: Session) -> OTPService:
    """Factory function to get OTP service"""
    return OTPService(db)
