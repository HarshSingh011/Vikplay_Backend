"""
Authentication module with clean architecture
"""
from .models import User, OTP, PendingRegistration
from .schemas import (
    UserRegister, UserLogin, TokenResponse, UserResponse,
    EmailVerify, OTPVerify, PasswordReset, MessageResponse
)
from .routes import router
from .services import get_user_service, get_otp_service
from .repositories import user_repository, otp_repository
from .utils import password_utils, jwt_utils, otp_utils, email_utils

__all__ = [
    # Models
    "User",
    "OTP",
    # Schemas
    "UserRegister",
    "UserLogin", 
    "TokenResponse",
    "UserResponse",
    "EmailVerify",
    "OTPVerify",
    "PasswordReset",
    "MessageResponse",
    # Routes
    "router",
    # Services
    "get_user_service",
    "get_otp_service",
    # Repositories
    "user_repository",
    "otp_repository",
    # Utils
    "password_utils",
    "jwt_utils",
    "otp_utils",
    "email_utils"
]