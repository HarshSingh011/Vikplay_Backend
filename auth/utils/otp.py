"""
OTP utilities for generating and managing OTPs
"""
import secrets
import string
from datetime import datetime, timedelta
from typing import Tuple


class OTPUtils:
    """Utility class for OTP operations"""
    
    @staticmethod
    def generate_otp(length: int = 6) -> str:
        """Generate a random numeric OTP"""
        digits = string.digits
        otp = ''.join(secrets.choice(digits) for _ in range(length))
        return otp
    
    @staticmethod
    def generate_alphanumeric_otp(length: int = 8) -> str:
        """Generate a random alphanumeric OTP"""
        characters = string.ascii_uppercase + string.digits
        otp = ''.join(secrets.choice(characters) for _ in range(length))
        return otp
    
    @staticmethod
    def calculate_expiry(minutes: int = 15) -> datetime:
        """Calculate OTP expiry time"""
        return datetime.utcnow() + timedelta(minutes=minutes)
    
    @staticmethod
    def is_expired(expiry_time: datetime) -> bool:
        """Check if OTP is expired"""
        return datetime.utcnow() > expiry_time
    
    @staticmethod
    def time_until_expiry(expiry_time: datetime) -> int:
        """Get seconds until OTP expires"""
        delta = expiry_time - datetime.utcnow()
        return max(0, int(delta.total_seconds()))
    
    @staticmethod
    def create_otp_with_expiry(length: int = 6, expiry_minutes: int = 15) -> Tuple[str, datetime]:
        """Create OTP with expiry time"""
        otp = OTPUtils.generate_otp(length)
        expiry = OTPUtils.calculate_expiry(expiry_minutes)
        return otp, expiry
    
    @staticmethod
    def validate_otp_format(otp: str, expected_length: int = 6) -> bool:
        """Validate OTP format"""
        if not otp:
            return False
        
        if len(otp) != expected_length:
            return False
        
        if not otp.isdigit():
            return False
        
        return True


# Global instance
otp_utils = OTPUtils()
