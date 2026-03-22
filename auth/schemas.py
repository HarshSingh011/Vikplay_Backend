from pydantic import BaseModel, EmailStr, validator, Field
from typing import Optional
from datetime import datetime
from auth.utils.validation_regex import (
    validate_email_regex, 
    validate_password_regex, 
    validate_username_regex
)

# User Schemas
class UserBase(BaseModel):
    username: str = Field(..., example="john_doe", description="Username (3-50 chars: letters, numbers, _, -, .)")
    email: str = Field(..., example="john@example.com", description="Valid email address")
    
    @validator('email')
    def validate_email(cls, v):
        if not validate_email_regex(v):
            raise ValueError('Invalid email format')
        return v

class UserCreate(UserBase):
    password: str = Field(
        ..., 
        min_length=8,
        example="SecurePass123!",
        description="Password (min 8 chars, must contain uppercase, lowercase, digit)"
    )
    
    @validator('password')
    def validate_password(cls, v):
        if not validate_password_regex(v):
            raise ValueError('Password must be at least 8 characters long and contain uppercase, lowercase, and digit')
        return v
    
    @validator('username')
    def validate_username(cls, v):
        if not validate_username_regex(v):
            raise ValueError('Username must be 3-50 characters with letters, numbers, underscore, hyphen, or dot')
        return v

# Alias for backward compatibility and clarity
UserRegister = UserCreate

class UserLogin(BaseModel):
    email: str = Field(..., example="john@example.com", description="Registered email address")
    password: str = Field(..., example="SecurePass123!", description="User password")
    
    @validator('email')
    def validate_login_email(cls, v):
        if not validate_email_regex(v):
            raise ValueError('Invalid email or password')
        return v
    
    @validator('password')
    def validate_login_password(cls, v):
        if not validate_password_regex(v):
            raise ValueError('Invalid email or password')
        return v

class UserResponse(UserBase):
    id: int
    is_active: bool
    is_verified: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# OTP Schemas
class OTPVerify(BaseModel):
    email: str = Field(..., example="john@example.com", description="Email address")
    otp: str = Field(..., example="123456", description="6-digit OTP code")
    
    @validator('email')
    def validate_otp_email(cls, v):
        if not validate_email_regex(v):
            raise ValueError('Invalid email format')
        return v
    
    @validator('otp')
    def validate_otp(cls, v):
        if len(v) != 6:
            raise ValueError('OTP must be 6 digits')
        if not v.isdigit():
            raise ValueError('OTP must contain only digits')
        return v

class EmailVerify(BaseModel):
    email: str = Field(..., example="john@example.com", description="Email address")
    
    @validator('email')
    def validate_email_verify(cls, v):
        if not validate_email_regex(v):
            raise ValueError('Invalid email format')
        return v

class PasswordReset(BaseModel):
    email: str = Field(..., example="john@example.com", description="Email address")
    new_password: str = Field(..., example="NewSecurePass123!", description="New password (min 8 chars, uppercase, lowercase, digit)")
    confirm_password: str = Field(..., example="NewSecurePass123!", description="Confirm new password")
    
    @validator('email')
    def validate_reset_email(cls, v):
        if not validate_email_regex(v):
            raise ValueError('Invalid email format')
        return v
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if not validate_password_regex(v):
            raise ValueError('Password must be at least 8 characters long and contain uppercase, lowercase, and digit')
        return v
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v

# Response Schemas
class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class MessageResponse(BaseModel):
    message: str
    success: bool = True
