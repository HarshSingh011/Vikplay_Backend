import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Optional
import bcrypt
import jwt
from sqlalchemy.orm import Session
from auth.models import User, OTP
import os
import logging

logger = logging.getLogger(__name__)

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Email Configuration
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
EMAIL_USERNAME = os.getenv("EMAIL_USERNAME", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", EMAIL_USERNAME)

class PasswordUtils:
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

class JWTUtils:
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
        """Create a JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str):
        """Verify and decode a JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.PyJWTError:
            return None

class OTPUtils:
    @staticmethod
    def generate_otp() -> str:
        """Generate a 6-digit OTP"""
        return ''.join([str(secrets.randbelow(10)) for _ in range(6)])
    
    @staticmethod
    def create_otp(db: Session, email: str, otp_type: str) -> str:
        """Create and store OTP in database"""
        # Invalidate any existing OTPs for this email and type
        db.query(OTP).filter(
            OTP.email == email,
            OTP.otp_type == otp_type,
            OTP.is_used == False
        ).update({"is_used": True})
        
        # Generate new OTP
        otp_code = OTPUtils.generate_otp()
        expires_at = datetime.utcnow() + timedelta(minutes=10)  # OTP expires in 10 minutes
        
        # Store in database
        db_otp = OTP(
            email=email,
            otp_code=otp_code,
            otp_type=otp_type,
            expires_at=expires_at
        )
        db.add(db_otp)
        db.commit()
        
        return otp_code
    
    @staticmethod
    def verify_otp(db: Session, email: str, otp_code: str, otp_type: str) -> bool:
        """Verify OTP"""
        otp_record = db.query(OTP).filter(
            OTP.email == email,
            OTP.otp_code == otp_code,
            OTP.otp_type == otp_type,
            OTP.is_used == False,
            OTP.expires_at > datetime.utcnow()
        ).first()
        
        if otp_record:
            # Mark OTP as used
            otp_record.is_used = True
            db.commit()
            return True
        
        return False

class EmailUtils:
    @staticmethod
    def send_email(to_email: str, subject: str, body: str) -> bool:
        """Send email using SMTP"""
        try:
            msg = MIMEMultipart()
            msg['From'] = FROM_EMAIL
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'html'))
            
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
            text = msg.as_string()
            server.sendmail(FROM_EMAIL, to_email, text)
            server.quit()
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    @staticmethod
    def send_registration_otp(email: str, otp: str, username: str) -> bool:
        """Send registration OTP email"""
        subject = "VikPay - Verify Your Registration"
        body = f"""
        <html>
        <body>
            <h2>Welcome to VikPay, {username}!</h2>
            <p>Thank you for registering with us. To complete your registration, please verify your email address using the OTP below:</p>
            <div style="background-color: #f0f0f0; padding: 20px; text-align: center; margin: 20px 0;">
                <h3 style="color: #007bff; font-size: 24px; letter-spacing: 5px;">{otp}</h3>
            </div>
            <p>This OTP will expire in 10 minutes.</p>
            <p>If you didn't create an account with VikPay, please ignore this email.</p>
            <br>
            <p>Best regards,<br>VikPay Team</p>
        </body>
        </html>
        """
        return EmailUtils.send_email(email, subject, body)
    
    @staticmethod
    def send_password_reset_otp(email: str, otp: str) -> bool:
        """Send password reset OTP email"""
        subject = "VikPay - Password Reset Request"
        body = f"""
        <html>
        <body>
            <h2>Password Reset Request</h2>
            <p>We received a request to reset your password for your VikPay account. Use the OTP below to reset your password:</p>
            <div style="background-color: #f0f0f0; padding: 20px; text-align: center; margin: 20px 0;">
                <h3 style="color: #007bff; font-size: 24px; letter-spacing: 5px;">{otp}</h3>
            </div>
            <p>This OTP will expire in 10 minutes.</p>
            <p>If you didn't request a password reset, please ignore this email or contact support if you have concerns.</p>
            <br>
            <p>Best regards,<br>VikPay Team</p>
        </body>
        </html>
        """
        return EmailUtils.send_email(email, subject, body)

class UserUtils:
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Get user by email"""
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        """Get user by username"""
        return db.query(User).filter(User.username == username).first()
    
    @staticmethod
    def create_user(db: Session, username: str, email: str, password: str) -> User:
        """Create a new user"""
        hashed_password = PasswordUtils.hash_password(password)
        db_user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            is_active=True,
            is_verified=False
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    
    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        user = UserUtils.get_user_by_email(db, email)
        if not user:
            return None
        if not PasswordUtils.verify_password(password, user.hashed_password):
            return None
        return user
    
    @staticmethod
    def verify_user_email(db: Session, email: str) -> bool:
        """Mark user email as verified"""
        user = UserUtils.get_user_by_email(db, email)
        if user:
            user.is_verified = True
            db.commit()
            return True
        return False
    
    @staticmethod
    def update_user_password(db: Session, email: str, new_password: str) -> bool:
        """Update user password"""
        user = UserUtils.get_user_by_email(db, email)
        if user:
            user.hashed_password = PasswordUtils.hash_password(new_password)
            db.commit()
            return True
        return False
