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
        self.secret_key = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
        self.algorithm = "HS256"
        self.access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
        self.refresh_token_expire_days = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    
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
