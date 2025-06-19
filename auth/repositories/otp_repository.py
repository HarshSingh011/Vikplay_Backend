"""
OTP repository for OTP data access operations
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from auth.models import OTP
from auth.repositories.base import SQLAlchemyRepository


class OTPRepository(SQLAlchemyRepository[OTP]):
    """OTP repository with specific OTP operations"""
    
    def __init__(self):
        super().__init__(OTP)
    
    def create_otp(self, db: Session, email: str, otp_code: str, purpose: str, expires_at: datetime) -> OTP:
        """Create a new OTP"""
        otp_data = {
            "email": email,
            "otp_code": otp_code,
            "purpose": purpose,
            "expires_at": expires_at,
            "is_used": False,
            "created_at": datetime.utcnow()
        }
        return self.create(db, otp_data)
    
    def get_valid_otp(self, db: Session, email: str, otp_code: str, purpose: str) -> Optional[OTP]:
        """Get a valid (unused and not expired) OTP"""
        return db.query(OTP).filter(
            OTP.email == email,
            OTP.otp_code == otp_code,
            OTP.purpose == purpose,
            OTP.is_used == False,
            OTP.expires_at > datetime.utcnow()
        ).first()
    
    def get_latest_otp(self, db: Session, email: str, purpose: str) -> Optional[OTP]:
        """Get the latest OTP for an email and purpose"""
        return db.query(OTP).filter(
            OTP.email == email,
            OTP.purpose == purpose
        ).order_by(OTP.created_at.desc()).first()
    
    def mark_otp_as_used(self, db: Session, otp: OTP) -> OTP:
        """Mark OTP as used"""
        update_data = {
            "is_used": True,
            "used_at": datetime.utcnow()
        }
        return self.update(db, db_obj=otp, obj_in=update_data)
    
    def invalidate_user_otps(self, db: Session, email: str, purpose: str) -> int:
        """Invalidate all unused OTPs for a user and purpose"""
        count = db.query(OTP).filter(
            OTP.email == email,
            OTP.purpose == purpose,
            OTP.is_used == False
        ).update({"is_used": True, "used_at": datetime.utcnow()})
        db.commit()
        return count
    
    def cleanup_expired_otps(self, db: Session) -> int:
        """Remove expired OTPs"""
        count = db.query(OTP).filter(
            OTP.expires_at < datetime.utcnow()
        ).delete()
        db.commit()
        return count
    
    def get_user_otp_attempts(self, db: Session, email: str, purpose: str, since: datetime) -> int:
        """Get the number of OTP attempts for a user since a specific time"""
        return db.query(OTP).filter(
            OTP.email == email,
            OTP.purpose == purpose,
            OTP.created_at >= since
        ).count()
    
    def can_request_new_otp(self, db: Session, email: str, purpose: str, cooldown_minutes: int = 1) -> bool:
        """Check if user can request a new OTP (rate limiting)"""
        since = datetime.utcnow() - timedelta(minutes=cooldown_minutes)
        latest_otp = db.query(OTP).filter(
            OTP.email == email,
            OTP.purpose == purpose,
            OTP.created_at >= since
        ).first()
        return latest_otp is None


# Global instance
otp_repository = OTPRepository()
