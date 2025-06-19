from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime

# User Schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str
    
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
        if not v.isalnum():
            raise ValueError('Username must contain only alphanumeric characters')
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    is_verified: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# OTP Schemas
class OTPVerify(BaseModel):
    email: EmailStr
    otp: str
    
    @validator('otp')
    def validate_otp(cls, v):
        if len(v) != 6:
            raise ValueError('OTP must be 6 digits')
        if not v.isdigit():
            raise ValueError('OTP must contain only digits')
        return v

class EmailVerify(BaseModel):
    email: EmailStr

class PasswordReset(BaseModel):
    email: EmailStr
    otp: str
    new_password: str
    confirm_password: str
    
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
