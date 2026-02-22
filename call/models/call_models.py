"""
Database models for video calling feature.
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SQLEnum, Boolean, Integer
from sqlalchemy.orm import relationship
from database import Base
import enum
import uuid


class CallStatusEnum(enum.Enum):
    """Call status enumeration."""
    INITIATED = "initiated"
    RINGING = "ringing"
    ACTIVE = "active"
    ENDED = "ended"
    MISSED = "missed"
    DECLINED = "declined"


class ParticipantRoleEnum(enum.Enum):
    """Participant role in a call."""
    INITIATOR = "initiator"
    INVITEE = "invitee"


class ParticipantStatusEnum(enum.Enum):
    """Participant status in a call."""
    INVITED = "invited"
    RINGING = "ringing"
    JOINED = "joined"
    LEFT = "left"
    DECLINED = "declined"


class Call(Base):
    """
    Call model representing a video call session.
    Supports multi-party calls.
    """
    __tablename__ = "calls"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Call details
    status = Column(SQLEnum(CallStatusEnum), default=CallStatusEnum.INITIATED, nullable=False)
    is_group_call = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)  # When first person joins
    ended_at = Column(DateTime, nullable=True)
    
    # Metadata
    duration = Column(Integer, nullable=True)  # Duration in seconds
    
    # Relationships
    participants = relationship(
        "CallParticipant",
        back_populates="call",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Call(id={self.id}, status={self.status.value}, participants={len(self.participants)})>"


class CallParticipant(Base):
    """
    Participant in a call.
    Tracks user participation and status in a call.
    """
    __tablename__ = "call_participants"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Foreign keys
    call_id = Column(String, ForeignKey("calls.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Participant details
    role = Column(SQLEnum(ParticipantRoleEnum), nullable=False)
    status = Column(SQLEnum(ParticipantStatusEnum), default=ParticipantStatusEnum.INVITED, nullable=False)
    
    # WebRTC peer ID for signaling
    peer_id = Column(String, nullable=True)  # Unique identifier for WebRTC peer connection
    
    # Added by (for tracking who invited this participant)
    invited_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Timestamps
    invited_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    joined_at = Column(DateTime, nullable=True)
    left_at = Column(DateTime, nullable=True)
    
    # Relationships
    call = relationship("Call", back_populates="participants")
    user = relationship("User", foreign_keys=[user_id])
    invited_by = relationship("User", foreign_keys=[invited_by_user_id])

    def __repr__(self):
        return f"<CallParticipant(id={self.id}, user_id={self.user_id}, status={self.status.value})>"
