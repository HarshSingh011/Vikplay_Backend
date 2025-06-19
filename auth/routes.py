from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from database import get_db
from auth.schemas import (
    UserCreate, UserLogin, UserResponse, OTPVerify, 
    EmailVerify, PasswordReset, TokenResponse, MessageResponse
)
from auth.utils import (
    UserUtils, OTPUtils, EmailUtils, JWTUtils, PasswordUtils
)
from auth.models import User
import logging

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/auth",
    tags=["authentication"]
)

# Security scheme
security = HTTPBearer()

@router.post("/register", response_model=MessageResponse)
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user and send OTP for email verification
    """
    try:
        # Check if user already exists
        existing_user_email = UserUtils.get_user_by_email(db, user_data.email)
        if existing_user_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        existing_user_username = UserUtils.get_user_by_username(db, user_data.username)
        if existing_user_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        
        # Create user
        user = UserUtils.create_user(
            db=db,
            username=user_data.username,
            email=user_data.email,
            password=user_data.password
        )
        
        # Generate and send OTP
        otp = OTPUtils.create_otp(db, user_data.email, "registration")
        email_sent = EmailUtils.send_registration_otp(user_data.email, otp, user_data.username)
        
        if not email_sent:
            logger.warning(f"Failed to send registration OTP to {user_data.email}")
            # Don't fail registration if email fails, just log it
        
        logger.info(f"User registered successfully: {user_data.email}")
        return MessageResponse(
            message="Registration successful! Please check your email for OTP verification.",
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again."
        )

@router.post("/verify-registration", response_model=MessageResponse)
async def verify_registration_otp(otp_data: OTPVerify, db: Session = Depends(get_db)):
    """
    Verify OTP for user registration
    """
    try:
        # Verify OTP
        is_valid = OTPUtils.verify_otp(db, otp_data.email, otp_data.otp, "registration")
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired OTP"
            )
        
        # Mark user as verified
        user_verified = UserUtils.verify_user_email(db, otp_data.email)
        
        if not user_verified:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        logger.info(f"User email verified successfully: {otp_data.email}")
        return MessageResponse(
            message="Email verified successfully! You can now login.",
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

@router.post("/login", response_model=TokenResponse)
async def login_user(login_data: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate user and return access token
    """
    try:
        # Authenticate user
        user = UserUtils.authenticate_user(db, login_data.email, login_data.password)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        if not user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Please verify your email before logging in"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is deactivated"
            )
        
        # Create access token
        access_token = JWTUtils.create_access_token(
            data={"sub": user.email, "user_id": user.id}
        )
        
        logger.info(f"User logged in successfully: {user.email}")
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse.from_orm(user)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed. Please try again."
        )

@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(email_data: EmailVerify, db: Session = Depends(get_db)):
    """
    Send OTP for password reset if user exists
    """
    try:
        # Check if user exists
        user = UserUtils.get_user_by_email(db, email_data.email)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No account found with this email address"
            )
        
        # Generate and send OTP
        otp = OTPUtils.create_otp(db, email_data.email, "forgot_password")
        email_sent = EmailUtils.send_password_reset_otp(email_data.email, otp)
        
        if not email_sent:
            logger.warning(f"Failed to send password reset OTP to {email_data.email}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send OTP email. Please try again."
            )
        
        logger.info(f"Password reset OTP sent to: {email_data.email}")
        return MessageResponse(
            message="Password reset OTP sent to your email.",
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Forgot password error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process forgot password request. Please try again."
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
    Reset user password after OTP verification
    """
    try:
        # Verify OTP one more time for security
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

# Protected route example - get current user
@router.get("/me", response_model=UserResponse)
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Get current authenticated user information
    """
    try:
        # Verify token
        payload = JWTUtils.verify_token(credentials.credentials)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )
        
        # Get user
        user_email = payload.get("sub")
        if user_email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )
        
        user = UserUtils.get_user_by_email(db, user_email)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        return UserResponse.from_orm(user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get current user error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user information"
        )
