from pydantic import BaseModel, EmailStr, validator, Field
from typing import Optional
from datetime import datetime

# User Schemas
class UserBase(BaseModel):
    username: str = Field(..., example="john_doe", description="Username (3-50 chars: letters, numbers, _, -, .)")
    email: EmailStr = Field(..., example="john@example.com", description="Valid email address")

class UserCreate(UserBase):
    password: str = Field(
        ..., 
        min_length=8,
        example="SecurePass123!",
        description="Password (min 8 chars, must contain uppercase, lowercase, digit)"
    )
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v
    
    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters long')
        if len(v) > 50:
            raise ValueError('Username must be less than 50 characters')
        # Allow letters, numbers, underscore, hyphen, dot
        import re
        if not re.match(r'^[a-zA-Z0-9_.-]+$', v):
            raise ValueError('Username can only contain letters, numbers, underscore, hyphen, and dot')
        return v

# Alias for backward compatibility and clarity
UserRegister = UserCreate

class UserLogin(BaseModel):
    email: EmailStr = Field(..., example="john@example.com", description="Registered email address")
    password: str = Field(..., example="SecurePass123!", description="User password")

class UserResponse(UserBase):
    id: int
    is_active: bool
    is_verified: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# OTP Schemas
class OTPVerify(BaseModel):
    email: EmailStr = Field(..., example="john@example.com", description="Email address")
    otp: str = Field(..., example="123456", description="6-digit OTP code")
    
    @validator('otp')
    def validate_otp(cls, v):
        if len(v) != 6:
            raise ValueError('OTP must be 6 digits')
        if not v.isdigit():
            raise ValueError('OTP must contain only digits')
        return v

class EmailVerify(BaseModel):
    email: EmailStr = Field(..., example="john@example.com", description="Email address")

class PasswordReset(BaseModel):
    email: EmailStr = Field(..., example="john@example.com", description="Email address")
    otp: str = Field(..., example="123456", description="6-digit OTP code")
    new_password: str = Field(..., example="NewSecurePass123!", description="New password (min 8 chars, uppercase, lowercase, digit)")
    confirm_password: str = Field(..., example="NewSecurePass123!", description="Confirm new password")
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v
    
    @validator('otp')
    def validate_otp(cls, v):
        if len(v) != 6:
            raise ValueError('OTP must be 6 digits')
        if not v.isdigit():
            raise ValueError('OTP must contain only digits')
        return v

# Response Schemas
class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class MessageResponse(BaseModel):
    message: str
    success: bool = True
