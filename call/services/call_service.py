"""
Service layer for call business logic.
"""
from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi import HTTPException, status

from call.repositories.call_repository import CallRepository
from call.models.call_models import (
    Call,
    CallParticipant,
    CallStatusEnum,
    ParticipantStatusEnum,
    ParticipantRoleEnum
)
from call.schemas.call_schemas import (
    CallCreate,
    CallInvite,
    CallResponse,
    ParticipantResponse
)
from auth.repositories.user_repository import UserRepository


class CallService:
    """Service for managing calls."""

    def __init__(self, db: Session):
        self.db = db
        self.call_repo = CallRepository(db)
        self.user_repo = UserRepository()

    def create_call(
        self,
        current_user_id: str,
        call_data: CallCreate
    ) -> Call:
        """
        Create a new call and invite participants.
        
        Args:
            current_user_id: ID of the user initiating the call
            call_data: Call creation data with phone numbers
            
        Returns:
            Created call with participants
        """
        # Determine if it's a group call
        is_group_call = len(call_data.phone_numbers) > 1 or call_data.is_group_call
        
        # Create the call
        call = self.call_repo.create_call(
            status=CallStatusEnum.INITIATED,
            is_group_call=is_group_call
        )
        
        # Add the initiator as a participant
        self.call_repo.add_participant(
            call_id=call.id,
            user_id=current_user_id,
            role=ParticipantRoleEnum.INITIATOR,
            status=ParticipantStatusEnum.JOINED
        )
        
        # Invite other participants
        for phone_number in call_data.phone_numbers:
            # Find user by phone number
            user = self.user_repo.get_by_phone(self.db, phone_number)
            
            if not user:
                # Skip if user not found - could log this
                continue
            
            # Don't add the initiator again
            if user.id == current_user_id:
                continue
            
            # Add participant
            self.call_repo.add_participant(
                call_id=call.id,
                user_id=user.id,
                role=ParticipantRoleEnum.INVITEE,
                invited_by_user_id=current_user_id,
                status=ParticipantStatusEnum.INVITED
            )
        
        # Update call status to ringing
        call = self.call_repo.update_call_status(call.id, CallStatusEnum.RINGING)
        
        return call

    def invite_participants(
        self,
        current_user_id: str,
        invite_data: CallInvite
    ) -> Call:
        """
        Invite additional participants to an ongoing call.
        Only existing participants can invite others.
        
        Args:
            current_user_id: ID of the user inviting participants
            invite_data: Invitation data with phone numbers
            
        Returns:
            Updated call
        """
        # Get the call
        call = self.call_repo.get_call_by_id(invite_data.call_id)
        if not call:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Call not found"
            )
        
        # Verify the user is a participant in the call
        participant = self.call_repo.get_participant(invite_data.call_id, current_user_id)
        if not participant:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a participant in this call"
            )
        
        # Verify call is active
        if call.status not in [CallStatusEnum.RINGING, CallStatusEnum.ACTIVE]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Call is not active"
            )
        
        # Invite new participants
        for phone_number in invite_data.phone_numbers:
            user = self.user_repo.get_by_phone(self.db, phone_number)
            
            if not user:
                continue
            
            # Check if already a participant
            if self.call_repo.participant_exists(call.id, user.id):
                continue
            
            # Add participant
            self.call_repo.add_participant(
                call_id=call.id,
                user_id=user.id,
                role=ParticipantRoleEnum.INVITEE,
                invited_by_user_id=current_user_id,
                status=ParticipantStatusEnum.INVITED
            )
        
        # Mark as group call if multiple participants
        if not call.is_group_call and len(call.participants) > 2:
            call.is_group_call = True
            self.db.commit()
        
        return self.call_repo.get_call_by_id(call.id)

    def join_call(
        self,
        user_id: str,
        call_id: str,
        peer_id: str
    ) -> Call:
        """
        User joins a call.
        
        Args:
            user_id: ID of the user joining
            call_id: ID of the call
            peer_id: WebRTC peer ID
            
        Returns:
            Updated call
        """
        # Get the call
        call = self.call_repo.get_call_by_id(call_id)
        if not call:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Call not found"
            )
        
        # Verify the user is a participant
        participant = self.call_repo.get_participant(call_id, user_id)
        if not participant:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not invited to this call"
            )
        
        # Verify call is not ended
        if call.status == CallStatusEnum.ENDED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Call has ended"
            )
        
        # Update participant status
        self.call_repo.update_participant_status(
            participant.id,
            ParticipantStatusEnum.JOINED,
            peer_id=peer_id
        )
        
        # Update call status to active if this is the first join
        if call.status != CallStatusEnum.ACTIVE:
            call = self.call_repo.update_call_status(call_id, CallStatusEnum.ACTIVE)
        
        return call

    def leave_call(
        self,
        user_id: str,
        call_id: str
    ) -> Call:
        """
        User leaves a call.
        
        Args:
            user_id: ID of the user leaving
            call_id: ID of the call
            
        Returns:
            Updated call
        """
        # Get the call
        call = self.call_repo.get_call_by_id(call_id)
        if not call:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Call not found"
            )
        
        # Get participant
        participant = self.call_repo.get_participant(call_id, user_id)
        if not participant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="You are not a participant in this call"
            )
        
        # Update participant status
        self.call_repo.update_participant_status(
            participant.id,
            ParticipantStatusEnum.LEFT
        )
        
        # Check if all participants have left
        active_participants = self.call_repo.get_active_participants(call_id)
        if not active_participants:
            # End the call
            call = self.call_repo.update_call_status(call_id, CallStatusEnum.ENDED)
        
        return call

    def end_call(
        self,
        user_id: str,
        call_id: str
    ) -> Call:
        """
        End a call. Only the initiator can end the call for everyone.
        
        Args:
            user_id: ID of the user ending the call
            call_id: ID of the call
            
        Returns:
            Ended call
        """
        # Get the call
        call = self.call_repo.get_call_by_id(call_id)
        if not call:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Call not found"
            )
        
        # Verify the user is the initiator
        participant = self.call_repo.get_participant(call_id, user_id)
        if not participant or participant.role != ParticipantRoleEnum.INITIATOR:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the call initiator can end the call"
            )
        
        # End the call
        call = self.call_repo.update_call_status(call_id, CallStatusEnum.ENDED)
        
        # Mark all participants as left
        for p in call.participants:
            if p.status not in [ParticipantStatusEnum.LEFT, ParticipantStatusEnum.DECLINED]:
                self.call_repo.update_participant_status(
                    p.id,
                    ParticipantStatusEnum.LEFT
                )
        
        return call

    def decline_call(
        self,
        user_id: str,
        call_id: str
    ) -> Call:
        """
        Decline a call invitation.
        
        Args:
            user_id: ID of the user declining
            call_id: ID of the call
            
        Returns:
            Updated call
        """
        # Get the call
        call = self.call_repo.get_call_by_id(call_id)
        if not call:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Call not found"
            )
        
        # Get participant
        participant = self.call_repo.get_participant(call_id, user_id)
        if not participant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="You are not invited to this call"
            )
        
        # Update participant status
        self.call_repo.update_participant_status(
            participant.id,
            ParticipantStatusEnum.DECLINED
        )
        
        return call

    def get_call(self, call_id: str) -> Optional[Call]:
        """Get a call by ID."""
        return self.call_repo.get_call_by_id(call_id)

    def get_active_calls(self, user_id: str) -> List[Call]:
        """Get all active calls for a user."""
        return self.call_repo.get_active_calls_for_user(user_id)

    def get_call_history(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[List[Call], int]:
        """Get call history for a user."""
        return self.call_repo.get_call_history_for_user(user_id, skip, limit)

    def _convert_to_response(self, call: Call) -> CallResponse:
        """Convert Call model to CallResponse schema."""
        participants = [
            ParticipantResponse(
                id=p.id,
                user_id=p.user_id,
                phone_number=p.user.phone_number if p.user else None,
                full_name=p.user.full_name if p.user else None,
                role=p.role.value,
                status=p.status.value,
                peer_id=p.peer_id,
                invited_by_user_id=p.invited_by_user_id,
                invited_at=p.invited_at,
                joined_at=p.joined_at,
                left_at=p.left_at
            )
            for p in call.participants
        ]
        
        return CallResponse(
            id=call.id,
            status=call.status.value,
            is_group_call=call.is_group_call,
            created_at=call.created_at,
            started_at=call.started_at,
            ended_at=call.ended_at,
            duration=call.duration,
            participants=participants
        )
