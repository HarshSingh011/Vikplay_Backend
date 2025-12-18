"""
Repository layer for call database operations.
"""
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc
from typing import List, Optional
from datetime import datetime

from call.models.call_models import (
    Call,
    CallParticipant,
    CallStatusEnum,
    ParticipantStatusEnum,
    ParticipantRoleEnum
)


class CallRepository:
    """Repository for call-related database operations."""

    def __init__(self, db: Session):
        self.db = db

    # Call operations

    def create_call(
        self,
        status: CallStatusEnum = CallStatusEnum.INITIATED,
        is_group_call: bool = False
    ) -> Call:
        """Create a new call."""
        call = Call(
            status=status,
            is_group_call=is_group_call
        )
        self.db.add(call)
        self.db.commit()
        self.db.refresh(call)
        return call

    def get_call_by_id(self, call_id: str) -> Optional[Call]:
        """Get a call by ID with participants."""
        return (
            self.db.query(Call)
            .options(joinedload(Call.participants))
            .filter(Call.id == call_id)
            .first()
        )

    def update_call_status(self, call_id: str, status: CallStatusEnum) -> Optional[Call]:
        """Update call status."""
        call = self.get_call_by_id(call_id)
        if call:
            call.status = status
            if status == CallStatusEnum.ACTIVE and not call.started_at:
                call.started_at = datetime.utcnow()
            elif status == CallStatusEnum.ENDED and not call.ended_at:
                call.ended_at = datetime.utcnow()
                if call.started_at:
                    call.duration = int((call.ended_at - call.started_at).total_seconds())
            self.db.commit()
            self.db.refresh(call)
        return call

    def get_active_calls_for_user(self, user_id: str) -> List[Call]:
        """Get all active calls for a user."""
        return (
            self.db.query(Call)
            .join(CallParticipant)
            .filter(
                and_(
                    CallParticipant.user_id == user_id,
                    Call.status.in_([CallStatusEnum.INITIATED, CallStatusEnum.RINGING, CallStatusEnum.ACTIVE])
                )
            )
            .options(joinedload(Call.participants))
            .all()
        )

    def get_call_history_for_user(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[List[Call], int]:
        """Get call history for a user with pagination."""
        query = (
            self.db.query(Call)
            .join(CallParticipant)
            .filter(CallParticipant.user_id == user_id)
            .options(joinedload(Call.participants))
            .order_by(desc(Call.created_at))
        )
        
        total = query.count()
        calls = query.offset(skip).limit(limit).all()
        
        return calls, total

    # Participant operations

    def add_participant(
        self,
        call_id: str,
        user_id: str,
        role: ParticipantRoleEnum,
        invited_by_user_id: Optional[str] = None,
        status: ParticipantStatusEnum = ParticipantStatusEnum.INVITED
    ) -> CallParticipant:
        """Add a participant to a call."""
        participant = CallParticipant(
            call_id=call_id,
            user_id=user_id,
            role=role,
            status=status,
            invited_by_user_id=invited_by_user_id
        )
        self.db.add(participant)
        self.db.commit()
        self.db.refresh(participant)
        return participant

    def get_participant(
        self,
        call_id: str,
        user_id: str
    ) -> Optional[CallParticipant]:
        """Get a specific participant in a call."""
        return (
            self.db.query(CallParticipant)
            .filter(
                and_(
                    CallParticipant.call_id == call_id,
                    CallParticipant.user_id == user_id
                )
            )
            .first()
        )

    def get_participant_by_peer_id(
        self,
        call_id: str,
        peer_id: str
    ) -> Optional[CallParticipant]:
        """Get a participant by their peer ID."""
        return (
            self.db.query(CallParticipant)
            .filter(
                and_(
                    CallParticipant.call_id == call_id,
                    CallParticipant.peer_id == peer_id
                )
            )
            .first()
        )

    def update_participant_status(
        self,
        participant_id: str,
        status: ParticipantStatusEnum,
        peer_id: Optional[str] = None
    ) -> Optional[CallParticipant]:
        """Update participant status."""
        participant = self.db.query(CallParticipant).filter(
            CallParticipant.id == participant_id
        ).first()
        
        if participant:
            participant.status = status
            if peer_id:
                participant.peer_id = peer_id
            
            if status == ParticipantStatusEnum.JOINED and not participant.joined_at:
                participant.joined_at = datetime.utcnow()
            elif status == ParticipantStatusEnum.LEFT and not participant.left_at:
                participant.left_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(participant)
        
        return participant

    def get_call_participants(self, call_id: str) -> List[CallParticipant]:
        """Get all participants of a call."""
        return (
            self.db.query(CallParticipant)
            .filter(CallParticipant.call_id == call_id)
            .all()
        )

    def get_active_participants(self, call_id: str) -> List[CallParticipant]:
        """Get all active participants in a call."""
        return (
            self.db.query(CallParticipant)
            .filter(
                and_(
                    CallParticipant.call_id == call_id,
                    CallParticipant.status.in_([
                        ParticipantStatusEnum.INVITED,
                        ParticipantStatusEnum.RINGING,
                        ParticipantStatusEnum.JOINED
                    ])
                )
            )
            .all()
        )

    def participant_exists(self, call_id: str, user_id: str) -> bool:
        """Check if a user is already a participant in the call."""
        return (
            self.db.query(CallParticipant)
            .filter(
                and_(
                    CallParticipant.call_id == call_id,
                    CallParticipant.user_id == user_id
                )
            )
            .first() is not None
        )
