"""
User authentication service
"""
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime

from auth.services.base import BaseService, ServiceResult, AuthenticationError, ValidationError, NotFoundError
from auth.repositories import user_repository
from auth.utils import password_utils, jwt_utils, email_utils
from auth.utils.pending_registration import PendingRegistration, RegistrationSession
from auth.models import User


class UserService(BaseService):
    """Service for user-related operations"""
    
    def __init__(self, db: Session):
        super().__init__(db)
        self.user_repo = user_repository
    
    def register_user(self, email: str, username: str, password: str) -> ServiceResult:
        """
        Register a new user (Step 1: Create pending registration and send OTP)
        User won't be created in DB until OTP is verified
        """
        try:
            # Validate input
            if not email or not username or not password:
                return ServiceResult.error_result("All fields are required")
            
            # Check email format
            if "@" not in email or "." not in email:
                return ServiceResult.error_result("Invalid email format")
            
            # Check password strength
            is_strong, password_errors = password_utils.is_strong_password(password)
            if not is_strong:
                return ServiceResult.error_result("Weak password", password_errors)
            
            # Check if user already exists in database
            existing_user = self.user_repo.get_by_email(self.db, email)
            if existing_user and existing_user.is_active:
                return ServiceResult.error_result("Email already registered and active")
            
            existing_username = self.user_repo.get_by_username(self.db, username)
            if existing_username and existing_username.is_active:
                return ServiceResult.error_result("Username already taken")
            
            # Check if there's a pending registration
            pending_info = PendingRegistration.get_pending_info(email)
            if pending_info:
                resend_count = pending_info['resend_count']
                time_remaining = pending_info['time_remaining_seconds']
                
                return ServiceResult.success_result(
                    data={
                        "status": "pending",
                        "message": "Registration already in progress. Please verify your email.",
                        "email": email,
                        "resend_count": resend_count,
                        "can_resend": True,
                        "expires_in_seconds": time_remaining
                    },
                    message="Registration pending. OTP already sent."
                )
            
            # Hash password
            hashed_password = password_utils.hash_password(password)
            
            # Create pending registration (stored in Redis)
            success = PendingRegistration.create_pending_registration(
                email=email,
                username=username,
                hashed_password=hashed_password
            )
            
            if not success:
                # Fallback: Create user directly without pending state
                user = self.user_repo.create_user(
                    self.db,
                    email=email,
                    username=username,
                    hashed_password=hashed_password
                )
                
                return ServiceResult.success_result(
                    data={
                        "user_id": user.id,
                        "email": user.email,
                        "username": user.username,
                        "is_active": user.is_active,
                        "status": "created_pending_verification"
                    },
                    message="User registered. Please verify your email."
                )
            
            return ServiceResult.success_result(
                data={
                    "status": "pending",
                    "email": email,
                    "username": username,
                    "message": "Registration initiated. Please verify OTP sent to your email."
                },
                message="Registration initiated successfully. Check your email for OTP."
            )
            
        except Exception as e:
            return ServiceResult.error_result(f"Registration failed: {str(e)}")
    
    def authenticate_user(self, email: str, password: str) -> ServiceResult:
        """Authenticate user login"""
        try:
            # Validate input
            if not email or not password:
                return ServiceResult.error_result("Email and password are required")
            
            # Get user
            user = self.user_repo.get_by_email(self.db, email)
            if not user:
                return ServiceResult.error_result("Invalid email or password")
            
            # Check password
            if not password_utils.verify_password(password, user.hashed_password):
                return ServiceResult.error_result("Invalid email or password")
            
            # Check if user is active
            if not user.is_active:
                return ServiceResult.error_result("Account not activated. Please verify your email.")
            
            # Update last login
            self.user_repo.update_last_login(self.db, user)
            
            # Generate tokens
            token_data = {
                "sub": user.id,
                "email": user.email,
                "username": user.username
            }
            
            access_token = jwt_utils.create_access_token(token_data)
            refresh_token = jwt_utils.create_refresh_token({"sub": user.id})
            
            return ServiceResult.success_result(
                data={
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "token_type": "bearer",
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "username": user.username,
                        "is_verified": user.is_verified
                    }
                },
                message="Login successful"
            )
            
        except Exception as e:
            return ServiceResult.error_result(f"Authentication failed: {str(e)}")
    
    def get_user_by_token(self, token: str) -> ServiceResult:
        """Get user information from token"""
        try:
            # Verify token
            payload = jwt_utils.verify_token(token)
            if not payload:
                return ServiceResult.error_result("Invalid or expired token")
            
            # Get user by email (token contains email in 'sub' field)
            user_email = payload.get("sub")
            if not user_email:
                return ServiceResult.error_result("Invalid token payload")
            
            user = self.user_repo.get_by_email(self.db, user_email)
            if not user:
                return ServiceResult.error_result("User not found")
            
            # Return the actual User object instead of a dict
            return ServiceResult.success_result(data=user)
            
        except Exception as e:
            return ServiceResult.error_result(f"Failed to get user: {str(e)}")
    
    def refresh_access_token(self, refresh_token: str) -> ServiceResult:
        """Refresh access token using refresh token"""
        try:
            # Verify refresh token
            payload = jwt_utils.verify_token(refresh_token, "refresh")
            if not payload:
                return ServiceResult.error_result("Invalid or expired refresh token")
            
            # Get user
            user_id = payload.get("sub")
            user = self.user_repo.get(self.db, user_id)
            if not user or not user.is_active:
                return ServiceResult.error_result("User not found or inactive")
            
            # Generate new access token
            token_data = {
                "sub": user.id,
                "email": user.email,
                "username": user.username
            }
            
            new_access_token = jwt_utils.create_access_token(token_data)
            
            return ServiceResult.success_result(
                data={
                    "access_token": new_access_token,
                    "token_type": "bearer"
                },
                message="Token refreshed successfully"
            )
            
        except Exception as e:
            return ServiceResult.error_result(f"Token refresh failed: {str(e)}")
    
    def activate_user(self, user_id: int) -> ServiceResult:
        """Activate user account"""
        try:
            user = self.user_repo.get(self.db, user_id)
            if not user:
                return ServiceResult.error_result("User not found")
            
            if user.is_active:
                return ServiceResult.error_result("User already activated")
            
            # Activate user
            self.user_repo.activate_user(self.db, user)
            
            # Send welcome email
            email_utils.send_welcome_email(user.email, user.username)
            
            return ServiceResult.success_result(
                message="User activated successfully"
            )
            
        except Exception as e:
            return ServiceResult.error_result(f"Activation failed: {str(e)}")
    
    def update_password(self, user_id: int, new_password: str) -> ServiceResult:
        """Update user password"""
        try:
            user = self.user_repo.get(self.db, user_id)
            if not user:
                return ServiceResult.error_result("User not found")
            
            # Check password strength
            is_strong, password_errors = password_utils.is_strong_password(new_password)
            if not is_strong:
                return ServiceResult.error_result("Weak password", password_errors)
            
            # Hash new password
            hashed_password = password_utils.hash_password(new_password)
            
            # Update password
            self.user_repo.update_password(self.db, user, hashed_password)
              # Send confirmation email
            email_utils.send_password_reset_confirmation(user.email, user.username)
            
            return ServiceResult.success_result(
                message="Password updated successfully"
            )
            
        except Exception as e:
            return ServiceResult.error_result(f"Password update failed: {str(e)}")
    
    def create_user(self, username: str, email: str, password: str) -> User:
        """Create a new user (used by register_user)"""
        hashed_password = password_utils.hash_password(password)
        return self.user_repo.create_user(
            self.db,
            username=username,
            email=email,
            hashed_password=hashed_password
        )
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.user_repo.get_by_email(self.db, email)
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return self.user_repo.get_by_username(self.db, username)
    
    def verify_user_email(self, email: str) -> ServiceResult:
        """Mark user email as verified"""
        try:
            user = self.user_repo.get_by_email(self.db, email)
            if not user:
                return ServiceResult.error_result("User not found")
            
            self.user_repo.verify_email(self.db, user)
            return ServiceResult.success_result(message="Email verified successfully")
            
        except Exception as e:
            return ServiceResult.error_result(f"Email verification failed: {str(e)}")
    
    def create_user_token(self, user: User) -> ServiceResult:
        """Create access token for user"""
        try:
            token = jwt_utils.create_access_token(data={"sub": user.email})
            return ServiceResult.success_result(data=token)
        except Exception as e:
            return ServiceResult.error_result(f"Token creation failed: {str(e)}")
    
    def update_user_password(self, email: str, new_password: str) -> ServiceResult:
        """Update user password by email"""
        try:
            user = self.user_repo.get_by_email(self.db, email)
            if not user:
                return ServiceResult.error_result("User not found")
            
            # Check password strength
            is_strong, password_errors = password_utils.is_strong_password(new_password)
            if not is_strong:
                return ServiceResult.error_result("Weak password", password_errors)
            
            # Hash new password
            hashed_password = password_utils.hash_password(new_password)
            
            # Update password
            self.user_repo.update_password(self.db, user, hashed_password)
            
            return ServiceResult.success_result(
                message="Password updated successfully"
            )
            
        except Exception as e:
            return ServiceResult.error_result(f"Password update failed: {str(e)}")


def get_user_service(db: Session) -> UserService:
    """Factory function to get user service"""
    return UserService(db)
