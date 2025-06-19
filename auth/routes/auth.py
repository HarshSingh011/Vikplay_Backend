"""
Authentication routes - register, login, verify
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from auth.schemas import (
    UserCreate, UserLogin, UserResponse, OTPVerify, 
    TokenResponse, MessageResponse
)
from auth.utils import (
    UserUtils, OTPUtils, EmailUtils, JWTUtils
)
import logging

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

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
        
        logger.info(f"Email verified successfully for: {otp_data.email}")
        return MessageResponse(
            message="Email verified successfully! You can now login.",
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Email verification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email verification failed. Please try again."
        )

@router.post("/login", response_model=TokenResponse)
async def login_user(user_data: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate user and return access token
    """
    try:
        # Authenticate user
        user = UserUtils.authenticate_user(db, user_data.email, user_data.password)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        if not user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Please verify your email first"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is disabled"
            )
        
        # Create access token
        access_token = JWTUtils.create_access_token(data={"sub": user.email})
        
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
