"""
Contact models for storing user contacts/favorites.
"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from auth.models import Base


class Contact(Base):
    """User's saved contact/favorite"""
    __tablename__ = "contacts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    contact_user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    nickname = Column(String(255), nullable=False)  # User-defined name for this contact
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Constraint: same user cannot add the same user twice as contact
    __table_args__ = (
        UniqueConstraint("user_id", "contact_user_id", name="user_contact_unique"),
    )

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "contact_user_id": self.contact_user_id,
            "nickname": self.nickname,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
