"""
Pydantic schemas for call operations.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class CallStatusEnum(str, Enum):
    """Call status enumeration."""
    INITIATED = "initiated"
    RINGING = "ringing"
    ACTIVE = "active"
    ENDED = "ended"
    MISSED = "missed"
    DECLINED = "declined"


class ParticipantRoleEnum(str, Enum):
    """Participant role enumeration."""
    INITIATOR = "initiator"
    INVITEE = "invitee"


class ParticipantStatusEnum(str, Enum):
    """Participant status enumeration."""
    INVITED = "invited"
    RINGING = "ringing"
    JOINED = "joined"
    LEFT = "left"
    DECLINED = "declined"


# Request Schemas

class CallCreate(BaseModel):
    """Schema for creating a new call."""
    phone_numbers: List[str] = Field(..., min_length=1, description="Phone numbers to call")
    is_group_call: Optional[bool] = Field(default=False, description="Whether this is a group call")

    @field_validator('phone_numbers')
    @classmethod
    def validate_phone_numbers(cls, v):
        if not v:
            raise ValueError("At least one phone number is required")
        # Basic validation - can be enhanced
        for phone in v:
            if not phone or not isinstance(phone, str):
                raise ValueError(f"Invalid phone number: {phone}")
        return v


class CallInvite(BaseModel):
    """Schema for inviting additional participants to an ongoing call."""
    call_id: str = Field(..., description="ID of the call")
    phone_numbers: List[str] = Field(..., min_length=1, description="Phone numbers to invite")

    @field_validator('phone_numbers')
    @classmethod
    def validate_phone_numbers(cls, v):
        if not v:
            raise ValueError("At least one phone number is required")
        return v


class CallJoin(BaseModel):
    """Schema for joining a call."""
    call_id: str = Field(..., description="ID of the call to join")
    peer_id: str = Field(..., description="WebRTC peer ID")


class CallEnd(BaseModel):
    """Schema for ending a call or leaving a call."""
    call_id: str = Field(..., description="ID of the call")


class GroupCallCreate(BaseModel):
    """Schema for creating a group call by user IDs."""
    user_ids: List[str] = Field(..., min_length=1, description="User IDs to call")


class SessionDescription(BaseModel):
    """WebRTC Session Description (SDP)."""
    type: str = Field(..., description="SDP type: offer or answer")
    sdp: str = Field(..., description="Session Description Protocol string")


class IceCandidate(BaseModel):
    """WebRTC ICE Candidate."""
    candidate: str = Field(..., description="ICE candidate string")
    sdpMid: Optional[str] = Field(None, description="Media stream identification")
    sdpMLineIndex: Optional[int] = Field(None, description="Media line index")


class WebRTCSignal(BaseModel):
    """WebRTC signaling message."""
    call_id: str = Field(..., description="Call ID")
    from_peer_id: str = Field(..., description="Sender peer ID")
    to_peer_id: str = Field(..., description="Target peer ID")
    signal_type: str = Field(..., description="Signal type: offer, answer, ice-candidate")
    data: Dict[str, Any] = Field(..., description="Signal data (SDP or ICE candidate)")


# Response Schemas

class ParticipantResponse(BaseModel):
    """Response schema for call participant."""
    id: str
    user_id: str
    phone_number: Optional[str] = None
    full_name: Optional[str] = None
    role: ParticipantRoleEnum
    status: ParticipantStatusEnum
    peer_id: Optional[str] = None
    invited_by_user_id: Optional[str] = None
    invited_at: datetime
    joined_at: Optional[datetime] = None
    left_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CallResponse(BaseModel):
    """Response schema for a call."""
    id: str
    status: CallStatusEnum
    is_group_call: bool
    created_at: datetime
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    duration: Optional[int] = None
    participants: List[ParticipantResponse] = []

    class Config:
        from_attributes = True


class CallListResponse(BaseModel):
    """Response schema for list of calls."""
    calls: List[CallResponse]
    total: int
    page: int
    page_size: int


# WebSocket Message Schemas

class WSMessageType(str, Enum):
    """WebSocket message types."""
    # Call events
    CALL_INITIATED = "call_initiated"
    CALL_RINGING = "call_ringing"
    CALL_ACCEPTED = "call_accepted"
    CALL_DECLINED = "call_declined"
    CALL_ENDED = "call_ended"
    
    # Participant events
    PARTICIPANT_JOINED = "participant_joined"
    PARTICIPANT_LEFT = "participant_left"
    PARTICIPANT_INVITED = "participant_invited"
    
    # WebRTC signaling
    WEBRTC_OFFER = "webrtc_offer"
    WEBRTC_ANSWER = "webrtc_answer"
    WEBRTC_ICE_CANDIDATE = "webrtc_ice_candidate"
    
    # Errors
    ERROR = "error"


class WSMessage(BaseModel):
    """WebSocket message schema."""
    type: WSMessageType
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
