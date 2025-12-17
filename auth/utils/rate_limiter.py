"""
Redis-based rate limiter for OTP and authentication
Industry-standard rate limiting with multiple tiers
"""
from typing import Optional, Dict, Tuple
from datetime import datetime, timedelta
from enum import Enum
import json

from auth.utils.redis_client import get_redis


class RateLimitTier(Enum):
    """Rate limit tiers for different scenarios"""
    RESEND_COOLDOWN = "resend_cooldown"  # 30 seconds between resends
    ATTEMPT_LIMIT = "attempt_limit"      # 5 attempts per 15 minutes
    HOURLY_LIMIT = "hourly_limit"        # 3 OTPs per hour
    DAILY_LIMIT = "daily_limit"          # 10 OTPs per day


class RateLimiter:
    """Redis-based rate limiter with fallback to in-memory"""
    
    # Fallback in-memory storage when Redis is unavailable
    _memory_store: Dict[str, Dict] = {}
    
    @staticmethod
    def _get_key(prefix: str, identifier: str, tier: RateLimitTier) -> str:
        """Generate Redis key for rate limiting"""
        return f"ratelimit:{prefix}:{tier.value}:{identifier}"
    
    @staticmethod
    def check_rate_limit(
        identifier: str,
        tier: RateLimitTier,
        max_attempts: int,
        window_seconds: int,
        prefix: str = "otp"
    ) -> Tuple[bool, Optional[int]]:
        """
        Check if action is allowed under rate limit
        
        Args:
            identifier: Email or user ID
            tier: Rate limit tier
            max_attempts: Maximum attempts allowed
            window_seconds: Time window in seconds
            prefix: Prefix for Redis key (e.g., 'otp', 'login')
        
        Returns:
            Tuple of (is_allowed, seconds_until_reset)
        """
        redis_client = get_redis()
        key = RateLimiter._get_key(prefix, identifier, tier)
        
        if redis_client:
            return RateLimiter._check_redis(
                redis_client, key, max_attempts, window_seconds
            )
        else:
            return RateLimiter._check_memory(
                key, max_attempts, window_seconds
            )
    
    @staticmethod
    def _check_redis(
        redis_client,
        key: str,
        max_attempts: int,
        window_seconds: int
    ) -> Tuple[bool, Optional[int]]:
        """Check rate limit using Redis"""
        try:
            current = redis_client.get(key)
            
            if current is None:
                # First attempt
                redis_client.setex(key, window_seconds, 1)
                return True, None
            
            count = int(current)
            if count >= max_attempts:
                # Rate limit exceeded
                ttl = redis_client.ttl(key)
                return False, ttl if ttl > 0 else window_seconds
            
            # Increment counter
            redis_client.incr(key)
            return True, None
            
        except Exception as e:
            print(f"Redis rate limit error: {e}, falling back to allow")
            return True, None
    
    @staticmethod
    def _check_memory(
        key: str,
        max_attempts: int,
        window_seconds: int
    ) -> Tuple[bool, Optional[int]]:
        """Check rate limit using in-memory storage (fallback)"""
        now = datetime.utcnow()
        
        if key in RateLimiter._memory_store:
            data = RateLimiter._memory_store[key]
            expires_at = datetime.fromisoformat(data['expires_at'])
            
            if now > expires_at:
                # Window expired, reset
                RateLimiter._memory_store[key] = {
                    'count': 1,
                    'expires_at': (now + timedelta(seconds=window_seconds)).isoformat()
                }
                return True, None
            
            if data['count'] >= max_attempts:
                # Rate limit exceeded
                seconds_left = int((expires_at - now).total_seconds())
                return False, seconds_left
            
            # Increment counter
            data['count'] += 1
            return True, None
        else:
            # First attempt
            RateLimiter._memory_store[key] = {
                'count': 1,
                'expires_at': (now + timedelta(seconds=window_seconds)).isoformat()
            }
            return True, None
    
    @staticmethod
    def reset_rate_limit(identifier: str, tier: RateLimitTier, prefix: str = "otp") -> bool:
        """Reset rate limit for an identifier"""
        redis_client = get_redis()
        key = RateLimiter._get_key(prefix, identifier, tier)
        
        if redis_client:
            try:
                redis_client.delete(key)
                return True
            except:
                pass
        
        # Fallback to memory
        if key in RateLimiter._memory_store:
            del RateLimiter._memory_store[key]
        
        return True
    
    @staticmethod
    def get_remaining_time(identifier: str, tier: RateLimitTier, prefix: str = "otp") -> Optional[int]:
        """Get remaining time in seconds until rate limit resets"""
        redis_client = get_redis()
        key = RateLimiter._get_key(prefix, identifier, tier)
        
        if redis_client:
            try:
                ttl = redis_client.ttl(key)
                return ttl if ttl > 0 else None
            except:
                pass
        
        # Fallback to memory
        if key in RateLimiter._memory_store:
            data = RateLimiter._memory_store[key]
            expires_at = datetime.fromisoformat(data['expires_at'])
            now = datetime.utcnow()
            if now < expires_at:
                return int((expires_at - now).total_seconds())
        
        return None


class OTPRateLimiter:
    """Specialized rate limiter for OTP operations"""
    
    # Industry-standard limits
    RESEND_COOLDOWN_SECONDS = 30      # 30 seconds between resends
    ATTEMPT_LIMIT_COUNT = 5            # 5 attempts per 15 minutes
    ATTEMPT_WINDOW_SECONDS = 900       # 15 minutes
    HOURLY_LIMIT_COUNT = 3             # 3 OTPs per hour
    HOURLY_WINDOW_SECONDS = 3600       # 1 hour
    DAILY_LIMIT_COUNT = 10             # 10 OTPs per day
    DAILY_WINDOW_SECONDS = 86400       # 24 hours
    
    @staticmethod
    def can_send_otp(email: str) -> Tuple[bool, Optional[str]]:
        """
        Check if OTP can be sent to email
        Returns (can_send, error_message)
        """
        # Check resend cooldown (30 seconds)
        allowed, wait_time = RateLimiter.check_rate_limit(
            email,
            RateLimitTier.RESEND_COOLDOWN,
            max_attempts=1,
            window_seconds=OTPRateLimiter.RESEND_COOLDOWN_SECONDS
        )
        if not allowed:
            return False, f"Please wait {wait_time} seconds before requesting another OTP"
        
        # Check attempt limit (5 in 15 minutes)
        allowed, wait_time = RateLimiter.check_rate_limit(
            email,
            RateLimitTier.ATTEMPT_LIMIT,
            max_attempts=OTPRateLimiter.ATTEMPT_LIMIT_COUNT,
            window_seconds=OTPRateLimiter.ATTEMPT_WINDOW_SECONDS
        )
        if not allowed:
            minutes = wait_time // 60
            return False, f"Too many OTP requests. Please try again in {minutes} minutes"
        
        # Check hourly limit (3 per hour)
        allowed, wait_time = RateLimiter.check_rate_limit(
            email,
            RateLimitTier.HOURLY_LIMIT,
            max_attempts=OTPRateLimiter.HOURLY_LIMIT_COUNT,
            window_seconds=OTPRateLimiter.HOURLY_WINDOW_SECONDS
        )
        if not allowed:
            minutes = wait_time // 60
            return False, f"Hourly OTP limit reached. Please try again in {minutes} minutes"
        
        # Check daily limit (10 per day)
        allowed, wait_time = RateLimiter.check_rate_limit(
            email,
            RateLimitTier.DAILY_LIMIT,
            max_attempts=OTPRateLimiter.DAILY_LIMIT_COUNT,
            window_seconds=OTPRateLimiter.DAILY_WINDOW_SECONDS
        )
        if not allowed:
            hours = wait_time // 3600
            return False, f"Daily OTP limit reached. Please try again in {hours} hours"
        
        return True, None
    
    @staticmethod
    def can_verify_otp(email: str) -> Tuple[bool, Optional[str]]:
        """
        Check if OTP verification is allowed (prevent brute force)
        Returns (can_verify, error_message)
        """
        # Allow 10 verification attempts per 5 minutes
        allowed, wait_time = RateLimiter.check_rate_limit(
            email,
            RateLimitTier.ATTEMPT_LIMIT,
            max_attempts=10,
            window_seconds=300,
            prefix="otp_verify"
        )
        if not allowed:
            return False, f"Too many verification attempts. Please wait {wait_time} seconds"
        
        return True, None
    
    @staticmethod
    def reset_limits(email: str):
        """Reset all rate limits for an email (e.g., after successful verification)"""
        RateLimiter.reset_rate_limit(email, RateLimitTier.RESEND_COOLDOWN)
        RateLimiter.reset_rate_limit(email, RateLimitTier.ATTEMPT_LIMIT)
        RateLimiter.reset_rate_limit(email, RateLimitTier.ATTEMPT_LIMIT, prefix="otp_verify")
