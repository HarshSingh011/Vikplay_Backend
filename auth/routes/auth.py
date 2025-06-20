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
from auth.services import get_user_service, get_otp_service
import logging

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

@router.post("/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user and send OTP for email verification
    
    **Requirements:**
    - **email**: Valid email address
    - **username**: 3-50 alphanumeric characters, must be unique
    - **password**: Minimum 8 characters with at least:
        - One uppercase letter
        - One lowercase letter
        - One digit
    
    **Example Request:**
    ```json
    {
        "email": "john@example.com",
        "username": "john_doe",
        "password": "SecurePass123!"
    }
    ```
    """
    try:
        user_service = get_user_service(db)
        otp_service = get_otp_service(db)
          # Check if user already exists by email
        existing_user_email = user_service.get_user_by_email(user_data.email)
        if existing_user_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "message": "Email already registered",
                    "field": "email",
                    "error_code": "EMAIL_EXISTS"
                }
            )
        
        # Check if username is already taken
        existing_user_username = user_service.get_user_by_username(user_data.username)
        if existing_user_username:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "message": "Username already taken. Please choose a different username.",
                    "field": "username", 
                    "error_code": "USERNAME_EXISTS"
                }
            )
        
        # Create user
        user = user_service.create_user(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password
        )
          # Generate and send OTP
        result = otp_service.send_verification_otp(user_data.email)
        
        if not result.success:
            logger.warning(f"Failed to send registration OTP to {user_data.email}: {result.message}")
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
        user_service = get_user_service(db)
        otp_service = get_otp_service(db)
        
        # Verify OTP
        result = otp_service.verify_otp(otp_data.email, otp_data.otp, "registration")
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.message
            )
        
        # Mark user as verified
        verify_result = user_service.verify_user_email(otp_data.email)
        
        if not verify_result.success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=verify_result.message
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
        user_service = get_user_service(db)
        
        # Authenticate user
        result = user_service.authenticate_user(user_data.email, user_data.password)
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=result.message
            )
        
        user = result.data
        
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
        token_result = user_service.create_user_token(user)
        
        if not token_result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create access token"
            )
        
        logger.info(f"User logged in successfully: {user.email}")
        return TokenResponse(
            access_token=token_result.data,
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
