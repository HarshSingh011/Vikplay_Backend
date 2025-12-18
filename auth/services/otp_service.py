"""
OTP service for managing one-time passwords
"""
from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from auth.services.base import BaseService, ServiceResult, ValidationError, RateLimitError
from auth.repositories import otp_repository, user_repository
from auth.utils import otp_utils, email_utils
from auth.utils.rate_limiter import OTPRateLimiter
from auth.utils.pending_registration import PendingRegistration

# Async email tasks (with fallback if Celery not available)
try:
    from auth.tasks.email_tasks import send_otp_email_async, send_welcome_email_async
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False


class OTPService(BaseService):
    """Service for OTP-related operations"""
    
    def __init__(self, db: Session):
        super().__init__(db)
        self.otp_repo = otp_repository
        self.user_repo = user_repository
    
    def send_verification_otp(self, email: str) -> ServiceResult:
        """Send OTP for email verification"""
        try:
            # Check Redis-based rate limiting (industry-standard)
            can_send, error_msg = OTPRateLimiter.can_send_otp(email)
            if not can_send:
                return ServiceResult.error_result(error_msg)
            
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
            
            # Send OTP via email asynchronously (or sync fallback)
            if CELERY_AVAILABLE:
                # Async email sending with Celery
                task = send_otp_email_async.delay(email, otp_code, "verification")
                email_sent = True  # Assume success, actual sending happens async
            else:
                # Fallback to synchronous sending
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
        """
        Verify OTP for email verification
        If there's a pending registration, complete it upon successful verification
        """
        try:
            # Check verification rate limiting (prevent brute force)
            can_verify, error_msg = OTPRateLimiter.can_verify_otp(email)
            if not can_verify:
                return ServiceResult.error_result(error_msg)
            
            # Validate OTP format
            if not otp_utils.validate_otp_format(otp_code, 6):
                return ServiceResult.error_result("Invalid OTP format")
            
            # Get valid OTP
            otp = self.otp_repo.get_valid_otp(self.db, email, otp_code, "verification")
            if not otp:
                return ServiceResult.error_result("Invalid or expired OTP")
            
            # Mark OTP as used
            self.otp_repo.mark_otp_as_used(self.db, otp)
            
            # Reset rate limits on successful verification
            OTPRateLimiter.reset_limits(email)
            
            # Check if there's a pending registration to complete
            pending_data = PendingRegistration.get_pending_registration(email)
            
            if pending_data:
                # Complete the registration by creating user in database
                try:
                    user = self.user_repo.create_user(
                        self.db,
                        email=pending_data['email'],
                        username=pending_data['username'],
                        hashed_password=pending_data['hashed_password']
                    )
                    
                    # Activate user immediately since OTP is verified
                    self.user_repo.activate_user(self.db, user)
                    
                    # Clean up pending registration
                    PendingRegistration.delete_pending_registration(email)
                    PendingRegistration.reset_resend_count(email)
                    
                    # Send welcome email asynchronously
                    if CELERY_AVAILABLE:
                        send_welcome_email_async.delay(user.email, user.username)
                    else:
                        email_utils.send_welcome_email(user.email, user.username)
                    
                    return ServiceResult.success_result(
                        data={
                            "email": email,
                            "user_id": user.id,
                            "username": user.username,
                            "user_created": True,
                            "user_activated": True
                        },
                        message="Registration completed successfully! Your account is now active."
                    )
                    
                except Exception as e:
                    # Clean up pending data on error
                    PendingRegistration.delete_pending_registration(email)
                    return ServiceResult.error_result(f"Failed to complete registration: {str(e)}")
            
            # No pending registration - just activate existing user
            user = self.user_repo.get_by_email(self.db, email)
            if user and not user.is_active:
                self.user_repo.activate_user(self.db, user)
                
                # Send welcome email asynchronously
                if CELERY_AVAILABLE:
                    send_welcome_email_async.delay(user.email, user.username)
                else:
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
                return ServiceResult.error_result("Email not registered")
            
            # Redis-based rate limiting
            can_send, error_msg = OTPRateLimiter.can_send_otp(email)
            if not can_send:
                return ServiceResult.error_result(error_msg)
            
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
            
            # Send OTP via email asynchronously
            if CELERY_AVAILABLE:
                send_otp_email_async.delay(email, otp_code, "password reset")
                email_sent = True
            else:
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
