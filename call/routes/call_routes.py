"""
API routes for call operations.
Includes REST endpoints and WebSocket for real-time signaling.
"""
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List
import logging

from database import get_db
from auth.utils.jwt_token import get_current_user
from auth.models import User
from call.services.call_service import CallService
from call.schemas.call_schemas import (
    CallCreate,
    CallResponse,
    CallInvite,
    CallJoin,
    CallEnd,
    CallListResponse,
    WebRTCSignal,
    WSMessageType
)
from call.utils.call_signaling_manager import call_signaling_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/calls", tags=["Calls"])


# REST Endpoints

@router.post("/", response_model=CallResponse, status_code=status.HTTP_201_CREATED)
async def create_call(
    call_data: CallCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new call and invite participants by phone number.
    
    - **phone_numbers**: List of phone numbers to call
    - **is_group_call**: Whether this is a group call
    
    Returns the created call with participant information.
    """
    service = CallService(db)
    call = service.create_call(current_user.id, call_data)
    
    # Notify invited participants via WebSocket
    for participant in call.participants:
        if participant.user_id != current_user.id:
            await call_signaling_manager.notify_incoming_call(
                user_id=participant.user_id,
                call_id=call.id,
                caller_info={
                    "user_id": current_user.id,
                    "full_name": current_user.full_name,
                    "phone_number": current_user.phone_number
                }
            )
    
    return service._convert_to_response(call)


@router.post("/invite", response_model=CallResponse)
async def invite_to_call(
    invite_data: CallInvite,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Invite additional participants to an ongoing call.
    Any participant can invite others.
    
    - **call_id**: ID of the call
    - **phone_numbers**: Phone numbers to invite
    """
    service = CallService(db)
    call = service.invite_participants(current_user.id, invite_data)
    
    # Notify newly invited participants
    for participant in call.participants:
        if participant.invited_by_user_id == current_user.id:
            await call_signaling_manager.notify_incoming_call(
                user_id=participant.user_id,
                call_id=call.id,
                caller_info={
                    "user_id": current_user.id,
                    "full_name": current_user.full_name,
                    "phone_number": current_user.phone_number
                }
            )
    
    # Notify existing participants about new invites
    await call_signaling_manager.broadcast_to_call(
        call_id=call.id,
        message={
            "type": WSMessageType.PARTICIPANT_INVITED.value,
            "data": {
                "call_id": call.id,
                "invited_by": current_user.id,
                "new_participants": len(invite_data.phone_numbers)
            }
        },
        exclude_user_id=current_user.id
    )
    
    return service._convert_to_response(call)


@router.post("/join", response_model=CallResponse)
async def join_call(
    join_data: CallJoin,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Join a call.
    
    - **call_id**: ID of the call to join
    - **peer_id**: WebRTC peer ID for this user
    """
    service = CallService(db)
    call = service.join_call(current_user.id, join_data.call_id, join_data.peer_id)
    
    # Add to signaling manager
    call_signaling_manager.add_to_call(call.id, current_user.id, join_data.peer_id)
    
    # Notify other participants
    await call_signaling_manager.notify_participant_joined(
        call_id=call.id,
        user_id=current_user.id,
        user_info={
            "user_id": current_user.id,
            "full_name": current_user.full_name,
            "phone_number": current_user.phone_number,
            "peer_id": join_data.peer_id
        }
    )
    
    return service._convert_to_response(call)


@router.post("/leave", response_model=CallResponse)
async def leave_call(
    leave_data: CallEnd,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Leave a call.
    
    - **call_id**: ID of the call to leave
    """
    service = CallService(db)
    call = service.leave_call(current_user.id, leave_data.call_id)
    
    # Remove from signaling manager
    call_signaling_manager.remove_from_call(leave_data.call_id, current_user.id)
    
    # Notify other participants
    await call_signaling_manager.notify_participant_left(
        call_id=leave_data.call_id,
        user_id=current_user.id
    )
    
    return service._convert_to_response(call)


@router.post("/end", response_model=CallResponse)
async def end_call(
    end_data: CallEnd,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    End a call. Only the call initiator can end the call.
    
    - **call_id**: ID of the call to end
    """
    service = CallService(db)
    call = service.end_call(current_user.id, end_data.call_id)
    
    # Notify all participants
    await call_signaling_manager.notify_call_ended(end_data.call_id)
    
    return service._convert_to_response(call)


@router.post("/decline", response_model=CallResponse)
async def decline_call(
    decline_data: CallEnd,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Decline a call invitation.
    
    - **call_id**: ID of the call to decline
    """
    service = CallService(db)
    call = service.decline_call(current_user.id, decline_data.call_id)
    
    # Notify other participants
    await call_signaling_manager.broadcast_to_call(
        call_id=decline_data.call_id,
        message={
            "type": WSMessageType.CALL_DECLINED.value,
            "data": {
                "call_id": decline_data.call_id,
                "user_id": current_user.id
            }
        }
    )
    
    return service._convert_to_response(call)


@router.get("/{call_id}", response_model=CallResponse)
async def get_call(
    call_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get details of a specific call.
    
    - **call_id**: ID of the call
    """
    service = CallService(db)
    call = service.get_call(call_id)
    
    if not call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Call not found"
        )
    
    # Verify user is a participant
    is_participant = any(p.user_id == current_user.id for p in call.participants)
    if not is_participant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a participant in this call"
        )
    
    return service._convert_to_response(call)


@router.get("/", response_model=List[CallResponse])
async def get_active_calls(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all active calls for the current user.
    """
    service = CallService(db)
    calls = service.get_active_calls(current_user.id)
    
    return [service._convert_to_response(call) for call in calls]


@router.get("/history/me", response_model=CallListResponse)
async def get_call_history(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get call history for the current user.
    
    - **skip**: Number of records to skip
    - **limit**: Maximum number of records to return
    """
    service = CallService(db)
    calls, total = service.get_call_history(current_user.id, skip, limit)
    
    return CallListResponse(
        calls=[service._convert_to_response(call) for call in calls],
        total=total,
        page=skip // limit + 1,
        page_size=limit
    )


# WebSocket for WebRTC Signaling

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str
):
    """
    WebSocket endpoint for WebRTC signaling.
    Handles real-time communication for call setup and peer connections.
    
    Query parameter:
    - **token**: JWT authentication token
    """
    # Authenticate user
    try:
        from auth.utils.jwt_token import verify_token
        payload = verify_token(token)
        user_id = payload.get("sub")
        if not user_id:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    except Exception as e:
        logger.error(f"WebSocket authentication failed: {e}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    # Connect user
    await call_signaling_manager.connect(websocket, user_id)
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_json()
            message_type = data.get("type")
            message_data = data.get("data", {})
            
            logger.info(f"Received WebSocket message from {user_id}: {message_type}")
            
            # Handle different message types
            if message_type == WSMessageType.WEBRTC_OFFER.value:
                # Forward WebRTC offer to target peer
                to_user_id = message_data.get("to_user_id")
                if to_user_id:
                    await call_signaling_manager.send_webrtc_signal(
                        from_user_id=user_id,
                        to_user_id=to_user_id,
                        signal_type=WSMessageType.WEBRTC_OFFER.value,
                        data=message_data.get("offer")
                    )
            
            elif message_type == WSMessageType.WEBRTC_ANSWER.value:
                # Forward WebRTC answer to target peer
                to_user_id = message_data.get("to_user_id")
                if to_user_id:
                    await call_signaling_manager.send_webrtc_signal(
                        from_user_id=user_id,
                        to_user_id=to_user_id,
                        signal_type=WSMessageType.WEBRTC_ANSWER.value,
                        data=message_data.get("answer")
                    )
            
            elif message_type == WSMessageType.WEBRTC_ICE_CANDIDATE.value:
                # Forward ICE candidate to target peer
                to_user_id = message_data.get("to_user_id")
                if to_user_id:
                    await call_signaling_manager.send_webrtc_signal(
                        from_user_id=user_id,
                        to_user_id=to_user_id,
                        signal_type=WSMessageType.WEBRTC_ICE_CANDIDATE.value,
                        data=message_data.get("candidate")
                    )
            
            else:
                logger.warning(f"Unknown message type: {message_type}")
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user_id}")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
    finally:
        # Disconnect user
        call_signaling_manager.disconnect(user_id)
