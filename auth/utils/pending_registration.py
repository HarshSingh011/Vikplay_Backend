"""
Pending registration state management using Redis
Tracks users who started registration but haven't verified email yet
"""
from typing import Optional, Dict
from datetime import datetime, timedelta
import json

from auth.utils.redis_client import get_redis


class PendingRegistration:
    """Manage pending user registrations"""
    
    # Key prefixes
    PENDING_PREFIX = "pending_reg"
    VERIFICATION_PREFIX = "verify_token"
    RESEND_COUNT_PREFIX = "resend_count"
    
    # TTLs
    PENDING_TTL = 86400  # 24 hours
    VERIFICATION_TTL = 900  # 15 minutes (same as OTP)
    RESEND_COUNT_TTL = 3600  # 1 hour
    
    @staticmethod
    def _get_key(prefix: str, identifier: str) -> str:
        """Generate Redis key"""
        return f"{prefix}:{identifier}"
    
    @classmethod
    def create_pending_registration(
        cls,
        email: str,
        username: str,
        hashed_password: str,
        full_name: Optional[str] = None
    ) -> bool:
        """
        Create or update pending registration
        
        Args:
            email: User's email
            username: User's username
            hashed_password: Hashed password
            full_name: User's full name
        
        Returns:
            True if created successfully
        """
        redis_client = get_redis()
        if not redis_client:
            return False
        
        key = cls._get_key(cls.PENDING_PREFIX, email)
        
        # Store user data temporarily
        data = {
            "email": email,
            "username": username,
            "hashed_password": hashed_password,
            "full_name": full_name,
            "created_at": datetime.utcnow().isoformat(),
            "status": "pending_verification"
        }
        
        try:
            redis_client.setex(
                key,
                cls.PENDING_TTL,
                json.dumps(data)
            )
            return True
        except:
            return False
    
    @classmethod
    def get_pending_registration(cls, email: str) -> Optional[Dict]:
        """
        Get pending registration data
        
        Returns:
            Dict with user data or None if not found
        """
        redis_client = get_redis()
        if not redis_client:
            return None
        
        key = cls._get_key(cls.PENDING_PREFIX, email)
        
        try:
            data = redis_client.get(key)
            if data:
                return json.loads(data)
        except:
            pass
        
        return None
    
    @classmethod
    def delete_pending_registration(cls, email: str) -> bool:
        """Delete pending registration"""
        redis_client = get_redis()
        if not redis_client:
            return False
        
        key = cls._get_key(cls.PENDING_PREFIX, email)
        
        try:
            redis_client.delete(key)
            return True
        except:
            return False
    
    @classmethod
    def mark_as_verified(cls, email: str) -> bool:
        """Mark registration as verified (ready to complete)"""
        redis_client = get_redis()
        if not redis_client:
            return False
        
        key = cls._get_key(cls.PENDING_PREFIX, email)
        
        try:
            data = redis_client.get(key)
            if data:
                user_data = json.loads(data)
                user_data['status'] = 'verified'
                user_data['verified_at'] = datetime.utcnow().isoformat()
                
                redis_client.setex(
                    key,
                    cls.PENDING_TTL,
                    json.dumps(user_data)
                )
                return True
        except:
            pass
        
        return False
    
    @classmethod
    def is_pending(cls, email: str) -> bool:
        """Check if email has pending registration"""
        return cls.get_pending_registration(email) is not None
    
    @classmethod
    def get_resend_count(cls, email: str) -> int:
        """Get number of OTP resends for this registration"""
        redis_client = get_redis()
        if not redis_client:
            return 0
        
        key = cls._get_key(cls.RESEND_COUNT_PREFIX, email)
        
        try:
            count = redis_client.get(key)
            return int(count) if count else 0
        except:
            return 0
    
    @classmethod
    def increment_resend_count(cls, email: str) -> int:
        """Increment resend counter"""
        redis_client = get_redis()
        if not redis_client:
            return 0
        
        key = cls._get_key(cls.RESEND_COUNT_PREFIX, email)
        
        try:
            count = redis_client.incr(key)
            redis_client.expire(key, cls.RESEND_COUNT_TTL)
            return count
        except:
            return 0
    
    @classmethod
    def reset_resend_count(cls, email: str) -> bool:
        """Reset resend counter"""
        redis_client = get_redis()
        if not redis_client:
            return False
        
        key = cls._get_key(cls.RESEND_COUNT_PREFIX, email)
        
        try:
            redis_client.delete(key)
            return True
        except:
            return False
    
    @classmethod
    def get_pending_info(cls, email: str) -> Optional[Dict]:
        """
        Get comprehensive pending registration info
        
        Returns dict with:
        - registration_data: User data
        - resend_count: Number of resends
        - time_remaining: Seconds until expiry
        """
        data = cls.get_pending_registration(email)
        if not data:
            return None
        
        redis_client = get_redis()
        time_remaining = None
        
        if redis_client:
            key = cls._get_key(cls.PENDING_PREFIX, email)
            try:
                ttl = redis_client.ttl(key)
                time_remaining = ttl if ttl > 0 else None
            except:
                pass
        
        return {
            "registration_data": data,
            "resend_count": cls.get_resend_count(email),
            "time_remaining_seconds": time_remaining,
            "expires_in_hours": round(time_remaining / 3600, 1) if time_remaining else None
        }


class RegistrationSession:
    """Manage registration session tokens for multi-step registration"""
    
    SESSION_PREFIX = "reg_session"
    SESSION_TTL = 1800  # 30 minutes
    
    @classmethod
    def create_session(cls, email: str, step: str = "otp_sent") -> Optional[str]:
        """Create registration session token"""
        redis_client = get_redis()
        if not redis_client:
            return None
        
        import secrets
        session_token = secrets.token_urlsafe(32)
        key = f"{cls.SESSION_PREFIX}:{session_token}"
        
        data = {
            "email": email,
            "step": step,
            "created_at": datetime.utcnow().isoformat()
        }
        
        try:
            redis_client.setex(key, cls.SESSION_TTL, json.dumps(data))
            return session_token
        except:
            return None
    
    @classmethod
    def get_session(cls, session_token: str) -> Optional[Dict]:
        """Get session data"""
        redis_client = get_redis()
        if not redis_client:
            return None
        
        key = f"{cls.SESSION_PREFIX}:{session_token}"
        
        try:
            data = redis_client.get(key)
            if data:
                return json.loads(data)
        except:
            pass
        
        return None
    
    @classmethod
    def update_session_step(cls, session_token: str, step: str) -> bool:
        """Update session step"""
        redis_client = get_redis()
        if not redis_client:
            return False
        
        data = cls.get_session(session_token)
        if not data:
            return False
        
        data['step'] = step
        data['updated_at'] = datetime.utcnow().isoformat()
        
        key = f"{cls.SESSION_PREFIX}:{session_token}"
        
        try:
            redis_client.setex(key, cls.SESSION_TTL, json.dumps(data))
            return True
        except:
            return False
    
    @classmethod
    def delete_session(cls, session_token: str) -> bool:
        """Delete session"""
        redis_client = get_redis()
        if not redis_client:
            return False
        
        key = f"{cls.SESSION_PREFIX}:{session_token}"
        
        try:
            redis_client.delete(key)
            return True
        except:
            return False
