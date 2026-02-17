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
from auth.models import User, OTP, PendingRegistration
import bcrypt
import jwt
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

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Email configuration
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
EMAIL_USERNAME = os.getenv("EMAIL_USERNAME", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", EMAIL_USERNAME)

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_access_token(data: dict) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({
        "exp": expire,
        "type": "access"  # Add type field for token verification
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

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

@router.post("/register", response_model=MessageResponse)
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user and send OTP for email verification.
    User will only be created in database after OTP verification.
    """
    logger.info(f"Registration request for email: {user_data.email}")
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )
        
        existing_username = db.query(User).filter(User.username == user_data.username).first()
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already taken"
            )
        
        # Check if there's already a pending registration for this email
        existing_pending = db.query(PendingRegistration).filter(
            PendingRegistration.email == user_data.email
        ).first()
        if existing_pending:
            # Remove old pending registration
            db.delete(existing_pending)
            db.commit()
        
        # Hash password
        hashed_password = hash_password(user_data.password)
        
        # Create pending registration record
        pending_registration = PendingRegistration(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            expires_at=datetime.utcnow() + timedelta(hours=24)  # 24 hour expiry
        )
        db.add(pending_registration)
        db.commit()
        
        # Generate and store OTP
        otp_code = generate_otp()
        expires_at = datetime.utcnow() + timedelta(minutes=10)  # 10 minute expiry
        
        otp_record = OTP(
            email=user_data.email,
            otp_code=otp_code,
            otp_type="registration",
            expires_at=expires_at
        )
        db.add(otp_record)
        db.commit()        # Send OTP email
        subject = "VikPay - Verify Your Registration"
        body = f"""
        <html>
        <body>
            <h2>Welcome to VikPay, {user_data.username}!</h2>
            <p>Thank you for registering with us. To complete your registration, please verify your email address using the OTP below:</p>
            <div style="background-color: #f0f0f0; padding: 20px; text-align: center; margin: 20px 0;">
                <h3 style="color: #007bff; font-size: 24px; letter-spacing: 5px;">{otp_code}</h3>
            </div>
            <p>This OTP will expire in 10 minutes.</p>            <p>If you didn't create an account with VikPay, please ignore this email.</p>
            <br>
            <p>Best regards,<br>VikPay Team</p>
        </body>
        </html>
        """
        email_sent = send_email(user_data.email, subject, body)
        
        if not email_sent:
            logger.warning(f"Failed to send registration OTP to {user_data.email}")
        
        logger.info(f"Pending registration created for: {user_data.email}")
        return MessageResponse(
            message="Registration initiated! Please check your email for OTP verification. Complete verification within 24 hours.",
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
    Verify OTP and create the actual user account in the database.
    """
    try:
        # Verify OTP
        otp_record = db.query(OTP).filter(
            OTP.email == otp_data.email,
            OTP.otp_code == otp_data.otp,
            OTP.otp_type == "registration",
            OTP.is_used == False,
            OTP.expires_at > datetime.utcnow()
        ).first()
        
        if not otp_record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired OTP"
            )
        
        # Get pending registration
        pending_registration = db.query(PendingRegistration).filter(
            PendingRegistration.email == otp_data.email,
            PendingRegistration.expires_at > datetime.utcnow()
        ).first()
        
        if not pending_registration:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Registration request expired. Please register again."
            )
        
        # Check if user already exists (double check)
        existing_user = db.query(User).filter(User.email == otp_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already exists"
            )
        
        # Create the actual user
        user = User(
            username=pending_registration.username,
            email=pending_registration.email,
            hashed_password=pending_registration.hashed_password,
            is_active=True,
            is_verified=True  # User is verified since they confirmed OTP
        )
        db.add(user)
        
        # Mark OTP as used
        otp_record.is_used = True
        
        # Delete pending registration
        db.delete(pending_registration)
        
        # Commit all changes
        db.commit()
        
        logger.info(f"User account created successfully for: {otp_data.email}")
        return MessageResponse(
            message="Account created successfully! You can now login.",
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
        # Get user from database
        user = db.query(User).filter(User.email == user_data.email).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
          # Verify password
        if not verify_password(user_data.password, user.hashed_password):
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
          # Create access token with user_id
        access_token = create_access_token(data={
            "sub": user.email,
            "user_id": user.id
        })
        
        logger.info(f"User logged in successfully: {user.email}")
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse.model_validate(user)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed. Please try again."
        )
