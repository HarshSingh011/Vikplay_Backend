"""
JWT token utilities for authentication
"""
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import os
import logging

logger = logging.getLogger(__name__)


class JWTUtils:
    """Utility class for JWT token operations"""
    
    def __init__(self):
        self.algorithm = "HS256"

    @property
    def secret_key(self):
        return os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")

    @property
    def access_token_expire_minutes(self):
        # Default: 43200 minutes = 30 days (1 month)
        return int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "43200"))

    @property
    def refresh_token_expire_days(self):
        return int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token"""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })
        
        try:
            encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
            return encoded_jwt
        except Exception as e:
            logger.error(f"Error creating access token: {e}")
            raise
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create a JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        })
        
        try:
            encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
            return encoded_jwt
        except Exception as e:
            logger.error(f"Error creating refresh token: {e}")
            raise
    
    def verify_token(self, token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Check token type
            if payload.get("type") != token_type:
                logger.warning(f"Invalid token type. Expected: {token_type}, Got: {payload.get('type')}")
                return None
            
            # Check expiration
            if datetime.utcnow().timestamp() > payload.get("exp", 0):
                logger.warning("Token has expired")
                return None
            
            return payload
        
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
        except Exception as e:
            logger.error(f"Error verifying token: {e}")
            return None
    
    def extract_user_id(self, token: str) -> Optional[int]:
        """Extract user ID from token"""
        payload = self.verify_token(token)
        if payload:
            return payload.get("sub")  # subject (user ID)
        return None
    
    def extract_email(self, token: str) -> Optional[str]:
        """Extract email from token"""
        payload = self.verify_token(token)
        if payload:
            return payload.get("email")
        return None
    
    def is_token_expired(self, token: str) -> bool:
        """Check if token is expired without decoding"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return datetime.utcnow().timestamp() > payload.get("exp", 0)
        except:
            return True


# Global instance
jwt_utils = JWTUtils()


# Utility functions for FastAPI dependency injection
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel


class TokenPayload(BaseModel):
    """Token payload model"""
    access_token: str


def verify_token_from_body(token_data: TokenPayload, db: Session) -> dict:
    """
    Verify access token from request body and return user data
    
    Args:
        token_data: Pydantic model containing access_token
        db: Database session
        
    Returns:
        User data from token
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        # Verify token
        payload = jwt_utils.verify_token(token_data.access_token, "access")
        
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired access token"
            )
        
        # Extract user info from payload
        user_data = {
            "user_id": payload.get("sub"),
            "email": payload.get("email"),
            "username": payload.get("username"),
            "exp": payload.get("exp"),
            "iat": payload.get("iat")
        }
        
        return user_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying token from body: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token"
        )


def get_current_user(credentials: HTTPAuthorizationCredentials, db: Session) -> dict:
    """
    Get current user from Authorization header
    
    Args:
        credentials: HTTP Authorization credentials
        db: Database session
        
    Returns:
        User data from token
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        # Verify token
        payload = jwt_utils.verify_token(credentials.credentials, "access")
        
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired access token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Extract user info from payload
        user_data = {
            "user_id": payload.get("sub"),
            "email": payload.get("email"),
            "username": payload.get("username"),
            "exp": payload.get("exp"),
            "iat": payload.get("iat")
        }
        
        return user_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
            headers={"WWW-Authenticate": "Bearer"}
        )
