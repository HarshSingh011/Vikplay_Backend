"""
API routes for call operations.
Includes REST endpoints and WebSocket for real-time signaling.
"""
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List
import logging

from database import get_db
from auth.utils.jwt_token import get_current_user, jwt_utils, HTTPBearer
from auth.models import User
from call.services.call_service import CallService

# Simplified dependency for call routes
security = HTTPBearer()

async def get_current_user_simple(credentials = Depends(security)) -> dict:
    """Get current user from token without requiring full User model"""
    payload = jwt_utils.verify_token(credentials.credentials, "access")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    return {
        "user_id": payload.get("user_id") or payload.get("sub"),
        "email": payload.get("sub"),
        "username": payload.get("username", "unknown")
    }

from call.schemas.call_schemas import (
    CallCreate,
    CallResponse,
    CallInvite,
    CallJoin,
    CallEnd,
    CallListResponse,
    WebRTCSignal,
    WSMessageType,
    GroupCallCreate
)
from call.schemas.contact_schemas import (
    ContactCreate,
    ContactUpdate
)
from call.utils.call_signaling_manager import call_signaling_manager
from call.models.contact_models import Contact

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/calls", tags=["Calls"])


# REST Endpoints

@router.post("/", response_model=CallResponse, status_code=status.HTTP_201_CREATED)
async def create_call(
    call_data: CallCreate,
    current_user: dict = Depends(get_current_user_simple),
    db: Session = Depends(get_db)
):
    """
    Create a new call and invite participants by phone number.
    
    - **phone_numbers**: List of phone numbers to call
    - **is_group_call**: Whether this is a group call
    
    Returns the created call with participant information.
    """
    service = CallService(db)
    call = service.create_call(current_user["user_id"], call_data)
    
    # Notify invited participants via WebSocket
    for participant in call.participants:
        if participant.user_id != current_user["user_id"]:
            await call_signaling_manager.notify_incoming_call(
                user_id=participant.user_id,
                call_id=call.id,
                caller_info={
                    "user_id": current_user["user_id"],
                    "full_name": current_user.full_name,
                    "phone_number": current_user.phone_number
                }
            )
    
    return service._convert_to_response(call)


@router.post("/invite", response_model=CallResponse)
async def invite_to_call(
    invite_data: CallInvite,
    current_user: dict = Depends(get_current_user_simple),
    db: Session = Depends(get_db)
):
    """
    Invite additional participants to an ongoing call.
    Any participant can invite others.
    
    - **call_id**: ID of the call
    - **phone_numbers**: Phone numbers to invite
    """
    service = CallService(db)
    call = service.invite_participants(current_user["user_id"], invite_data)
    
    # Notify newly invited participants
    for participant in call.participants:
        if participant.invited_by_user_id == current_user["user_id"]:
            await call_signaling_manager.notify_incoming_call(
                user_id=participant.user_id,
                call_id=call.id,
                caller_info={
                    "user_id": current_user["user_id"],
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
                "invited_by": current_user["user_id"],
                "new_participants": len(invite_data.phone_numbers)
            }
        },
        exclude_user_id=current_user["user_id"]
    )
    
    return service._convert_to_response(call)


@router.post("/join", response_model=CallResponse)
async def join_call(
    join_data: CallJoin,
    current_user: dict = Depends(get_current_user_simple),
    db: Session = Depends(get_db)
):
    """
    Join a call.
    
    - **call_id**: ID of the call to join
    - **peer_id**: WebRTC peer ID for this user
    """
    service = CallService(db)
    call = service.join_call(current_user["user_id"], join_data.call_id, join_data.peer_id)
    
    # Add to signaling manager
    call_signaling_manager.add_to_call(call.id, current_user["user_id"], join_data.peer_id)
    
    # Notify other participants
    await call_signaling_manager.notify_participant_joined(
        call_id=call.id,
        user_id=current_user["user_id"],
        user_info={
            "user_id": current_user["user_id"],
            "full_name": current_user.full_name,
            "phone_number": current_user.phone_number,
            "peer_id": join_data.peer_id
        }
    )
    
    return service._convert_to_response(call)


@router.post("/leave", response_model=CallResponse)
async def leave_call(
    leave_data: CallEnd,
    current_user: dict = Depends(get_current_user_simple),
    db: Session = Depends(get_db)
):
    """
    Leave a call.
    
    - **call_id**: ID of the call to leave
    """
    service = CallService(db)
    call = service.leave_call(current_user["user_id"], leave_data.call_id)
    
    # Remove from signaling manager
    call_signaling_manager.remove_from_call(leave_data.call_id, current_user["user_id"])
    
    # Notify other participants
    await call_signaling_manager.notify_participant_left(
        call_id=leave_data.call_id,
        user_id=current_user["user_id"]
    )
    
    return service._convert_to_response(call)


@router.post("/end", response_model=CallResponse)
async def end_call(
    end_data: CallEnd,
    current_user: dict = Depends(get_current_user_simple),
    db: Session = Depends(get_db)
):
    """
    End a call. Only the call initiator can end the call.
    
    - **call_id**: ID of the call to end
    """
    service = CallService(db)
    call = service.end_call(current_user["user_id"], end_data.call_id)
    
    # Notify all participants
    await call_signaling_manager.notify_call_ended(end_data.call_id)
    
    return service._convert_to_response(call)


@router.post("/decline", response_model=CallResponse)
async def decline_call(
    decline_data: CallEnd,
    current_user: dict = Depends(get_current_user_simple),
    db: Session = Depends(get_db)
):
    """
    Decline a call invitation.
    
    - **call_id**: ID of the call to decline
    """
    service = CallService(db)
    call = service.decline_call(current_user["user_id"], decline_data.call_id)
    
    # Notify other participants
    await call_signaling_manager.broadcast_to_call(
        call_id=decline_data.call_id,
        message={
            "type": WSMessageType.CALL_DECLINED.value,
            "data": {
                "call_id": decline_data.call_id,
                "user_id": current_user["user_id"]
            }
        }
    )
    
    return service._convert_to_response(call)


@router.get("/{call_id}", response_model=CallResponse)
async def get_call(
    call_id: str,
    current_user: dict = Depends(get_current_user_simple),
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
    is_participant = any(p.user_id == current_user["user_id"] for p in call.participants)
    if not is_participant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a participant in this call"
        )
    
    return service._convert_to_response(call)


@router.get("/", response_model=List[CallResponse])
async def get_active_calls(
    current_user: dict = Depends(get_current_user_simple),
    db: Session = Depends(get_db)
):
    """
    Get all active calls for the current user.
    """
    service = CallService(db)
    calls = service.get_active_calls(current_user["user_id"])
    
    return [service._convert_to_response(call) for call in calls]


@router.get("/history/me", response_model=CallListResponse)
async def get_call_history(
    skip: int = 0,
    limit: int = 50,
    current_user: dict = Depends(get_current_user_simple),
    db: Session = Depends(get_db)
):
    """
    Get call history for the current user.
    
    - **skip**: Number of records to skip
    - **limit**: Maximum number of records to return
    """
    service = CallService(db)
    calls, total = service.get_call_history(current_user["user_id"], skip, limit)
    
    return CallListResponse(
        calls=[service._convert_to_response(call) for call in calls],
        total=total,
        page=skip // limit + 1,
        page_size=limit
    )


@router.get("/users/search")
async def search_users_for_call(
    query: str = "",
    current_user: dict = Depends(get_current_user_simple),
    db: Session = Depends(get_db)
):
    """
    Search for users to call (like WhatsApp contact search).
    Returns active users matching the search query.
    """
    from auth.repositories.user_repository import user_repository
    
    if query:
        users = user_repository.search_users(db, query, skip=0, limit=200)
    else:
        # Get all users (regardless of active status) to show complete contact list
        # This allows calling users even if they haven't logged in yet
        users = db.query(User).limit(200).all()
    
    # Exclude current user - handle type conversion carefully
    current_uid = current_user["user_id"]
    # Ensure current_uid is an integer for comparison
    if isinstance(current_uid, str):
        try:
            current_uid = int(current_uid)
        except (ValueError, TypeError):
            current_uid = None  # Can't convert, include all users
    
    if current_uid is not None:
        users = [u for u in users if u.id != current_uid]
        logger.warning(f"[SEARCH] Excluding current user: {current_uid} (type: {type(current_uid).__name__}). Remaining users: {len(users)}")
    else:
        logger.warning(f"[SEARCH] Could not determine current_uid to exclude")
    
    # Build response with online user info from token (more accurate)
    result = []
    for user in users:
        user_id_str = str(user.id)
        is_online = call_signaling_manager.is_user_online(user_id_str)
        
        # If user is online, use their token info (more accurate than DB)
        # Otherwise use database info
        if is_online:
            online_info = call_signaling_manager.get_user_info(user_id_str)
            if online_info:
                result.append({
                    "id": user.id,
                    "username": online_info.get("username", user.username),
                    "email": online_info.get("email", user.email),
                    "phone_number": user.phone_number,
                    "is_online": True
                })
                continue
        
        # Fallback to database info
        result.append({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "phone_number": user.phone_number,
            "is_online": is_online
        })
    
    return result


@router.get("/me")
async def get_current_user(
    current_user: dict = Depends(get_current_user_simple),
    db: Session = Depends(get_db)
):
    """
    Get current user's information including their user ID.
    Useful for debugging and verification.
    """
    from auth.repositories.user_repository import user_repository
    
    user_id = current_user.get("user_id")
    if isinstance(user_id, str) and user_id.isdigit():
        user_id = int(user_id)
    
    # Try to get full user data from DB, but fall back to token data if not found
    user = user_repository.get(db, user_id)
    if user:
        return {
            "id": user.id,
            "user_id": str(user.id),
            "email": user.email,
            "username": user.username,
            "phone_number": user.phone_number,
            "full_name": user.full_name
        }
    
    # Fallback: return data from token (user is authenticated even if not fully in DB)
    return {
        "id": user_id,
        "user_id": str(user_id),
        "email": current_user.get("email", ""),
        "username": current_user.get("username", "User"),
        "phone_number": "",
        "full_name": current_user.get("username", "Unknown")
    }


@router.post("/call-user/{user_id}", response_model=CallResponse, status_code=status.HTTP_201_CREATED)
async def call_user_directly(
    user_id: str,
    current_user: dict = Depends(get_current_user_simple),
    db: Session = Depends(get_db)
):
    """
    Initiate a direct call to another user (like WhatsApp call).
    
    - **user_id**: The ID of the user to call
    """
    # Convert user_id to integer for database operations
    try:
        callee_user_id = int(user_id)
    except ValueError:
        logger.error(f"[CALL] Invalid user_id format: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    # Verify the callee exists
    from auth.repositories.user_repository import user_repository
    callee = user_repository.get(db, callee_user_id)
    if not callee:
        logger.error(f"[CALL] User not found: {callee_user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # If callee is not currently connected to the signaling server, return a clear error
    if not call_signaling_manager.is_user_online(str(callee_user_id)):
        logger.warning(f"[CALL] Callee {callee_user_id} is not connected. Active: {list(call_signaling_manager.active_connections.keys())}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Callee is not connected to the signaling server"
        )

    service = CallService(db)
    call = service.create_direct_call(str(current_user["user_id"]), str(callee_user_id))

    # Add caller to signaling manager so they are tracked in the call
    call_signaling_manager.add_to_call(str(call.id), str(current_user["user_id"]))

    # Log for debugging
    logger.warning(f"[CALL] Initiating direct call: from={current_user['user_id']} to={callee_user_id} call_id={call.id}")
    logger.warning(f"[CALL] Callee info: email={callee.email}, username={callee.username}")
    logger.warning(f"[CALL] Active WebSocket connections: {list(call_signaling_manager.active_connections.keys())}")

    # Notify the called user via WebSocket
    await call_signaling_manager.send_call_notification(
        to_user_id=str(callee_user_id),  # Send to INTEGER string representation
        call_id=str(call.id),
        from_user_id=str(current_user["user_id"]),
        from_username=current_user["username"]
    )

    logger.warning(f"[CALL] Notification sent to user {callee_user_id}")

    return service._convert_to_response(call)


@router.post("/group-call", response_model=CallResponse, status_code=status.HTTP_201_CREATED)
async def create_group_call(
    call_data: GroupCallCreate,
    current_user: dict = Depends(get_current_user_simple),
    db: Session = Depends(get_db)
):
    """
    Create a group call with multiple users.
    
    - **user_ids**: List of user IDs to invite
    """
    service = CallService(db)
    call = service.create_group_call_by_ids(current_user["user_id"], call_data.user_ids)
    
    # Add caller to signaling manager
    call_signaling_manager.add_to_call(str(call.id), str(current_user["user_id"]))
    
    # Notify each invited user
    for uid in call_data.user_ids:
        if str(uid) != str(current_user["user_id"]):
            await call_signaling_manager.send_to_user(str(uid), {
                "type": "INCOMING_CALL",
                "data": {
                    "call_id": str(call.id),
                    "from_user_id": str(current_user["user_id"]),
                    "from_username": current_user["username"],
                    "is_group_call": True,
                    "participant_count": len(call_data.user_ids)
                }
            })
    
    return service._convert_to_response(call)


# Contact Management Endpoints

@router.post("/contacts/add", response_model=dict, status_code=status.HTTP_201_CREATED)
async def add_contact(
    contact_data: ContactCreate,
    current_user: dict = Depends(get_current_user_simple),
    db: Session = Depends(get_db)
):
    """
    Add a user to your contact list with a nickname.
    
    Request body:
    {
      "email": "user@example.com",
      "nickname": "John"
    }
    """
    try:
        email = contact_data.email.strip()
        nickname = contact_data.nickname.strip()
        
        if not email or not nickname:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Both email and nickname are required"
            )
        
        # Find the contact user by email
        from auth.repositories.user_repository import user_repository
        contact_user = user_repository.get_by_email(db, email)
        
        if not contact_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with email {email} not found"
            )
        
        # Prevent adding yourself as contact
        current_uid = current_user["user_id"]
        if isinstance(current_uid, str):
            current_uid = int(current_uid)
        
        if contact_user.id == current_uid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot add yourself as a contact"
            )
        
        # Check if already exists
        from call.repositories.contact_repository import ContactRepository
        contact_repo = ContactRepository()
        existing = contact_repo.get_contact_by_users(db, current_uid, contact_user.id)
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"{email} is already in your contacts"
            )
        
        # Add contact
        contact = contact_repo.add_contact(
            db,
            user_id=current_uid,
            contact_user_id=contact_user.id,
            nickname=nickname
        )
        
        logger.info(f"[CONTACT] User {current_uid} added contact: {contact_user.email} as {nickname}")
        
        return {
            "success": True,
            "message": f"Contact added: {nickname}",
            "contact": {
                "id": contact.id,
                "contact_user_id": contact.contact_user_id,
                "contact_email": contact_user.email,
                "contact_username": contact_user.username,
                "nickname": contact.nickname
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding contact: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add contact"
        )


@router.get("/contacts")
async def get_contacts(
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(get_current_user_simple),
    db: Session = Depends(get_db)
):
    """
    Get your contact list.
    Returns all contacts with their latest online status.
    """
    try:
        current_uid = current_user["user_id"]
        if isinstance(current_uid, str):
            current_uid = int(current_uid)
        
        from call.repositories.contact_repository import ContactRepository
        from auth.repositories.user_repository import user_repository
        
        contact_repo = ContactRepository()
        contacts = contact_repo.get_contacts(db, current_uid, skip, limit)
        
        # Enrich with user info and online status
        result = []
        for contact in contacts:
            contact_user = user_repository.get(db, contact.contact_user_id)
            if contact_user:
                result.append({
                    "id": contact.id,
                    "contact_user_id": contact.contact_user_id,
                    "nickname": contact.nickname,
                    "email": contact_user.email,
                    "username": contact_user.username,
                    "phone_number": contact_user.phone_number,
                    "is_online": call_signaling_manager.is_user_online(str(contact.contact_user_id))
                })
        
        total = db.query(Contact).filter(Contact.user_id == current_uid).count()
        
        return {
            "contacts": result,
            "total": total,
            "page": skip // limit + 1 if limit > 0 else 1,
            "page_size": limit
        }
    
    except Exception as e:
        logger.error(f"Error fetching contacts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch contacts"
        )


@router.delete("/contacts/{contact_id}")
async def delete_contact(
    contact_id: str,
    current_user: dict = Depends(get_current_user_simple),
    db: Session = Depends(get_db)
):
    """
    Remove a contact from your contact list.
    """
    try:
        current_uid = current_user["user_id"]
        if isinstance(current_uid, str):
            current_uid = int(current_uid)
        
        from call.repositories.contact_repository import ContactRepository
        contact_repo = ContactRepository()
        contact = contact_repo.get_contact(db, contact_id)
        
        if not contact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contact not found"
            )
        
        # Verify ownership
        if contact.user_id != current_uid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot delete someone else's contact"
            )
        
        contact_repo.delete_contact(db, contact_id)
        
        logger.info(f"[CONTACT] User {current_uid} deleted contact: {contact_id}")
        
        return {
            "success": True,
            "message": "Contact deleted"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting contact: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete contact"
        )


@router.put("/contacts/{contact_id}", status_code=status.HTTP_200_OK)
async def update_contact(
    contact_id: str,
    update_data: ContactUpdate,
    current_user: dict = Depends(get_current_user_simple),
    db: Session = Depends(get_db)
):
    """
    Update a contact's nickname.
    
    Request body:
    {
      "nickname": "New Nickname"
    }
    """
    try:
        if not update_data.nickname:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nickname is required"
            )
        
        current_uid = current_user["user_id"]
        if isinstance(current_uid, str):
            current_uid = int(current_uid)
        
        from call.repositories.contact_repository import ContactRepository
        contact_repo = ContactRepository()
        contact = contact_repo.get_contact(db, contact_id)
        
        if not contact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contact not found"
            )
        
        # Verify ownership
        if contact.user_id != current_uid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot update someone else's contact"
            )
        
        updated = contact_repo.update_contact_nickname(db, contact_id, update_data.nickname)
        
        logger.info(f"[CONTACT] User {current_uid} updated contact: {contact_id} nickname to {updated.nickname}")
        
        return {
            "success": True,
            "message": "Contact updated",
            "nickname": updated.nickname
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating contact: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update contact"
        )


@router.post("/{call_id}/add-user/{user_id}", response_model=CallResponse)
async def add_user_to_call(
    call_id: str,
    user_id: str,
    current_user: dict = Depends(get_current_user_simple),
    db: Session = Depends(get_db)
):
    """
    Add a person to an ongoing call. Any participant can add others.

    - **call_id**: The active call ID
    - **user_id**: The user to add
    """
    service = CallService(db)
    call = service.add_user_to_existing_call(current_user["user_id"], call_id, user_id)

    # Send incoming-call notification to the new user
    await call_signaling_manager.send_to_user(str(user_id), {
        "type": "INCOMING_CALL",
        "data": {
            "call_id": str(call.id),
            "from_user_id": str(current_user["user_id"]),
            "from_username": current_user["username"],
            "is_group_call": call.is_group_call,
            "participant_count": len(call.participants)
        }
    })

    return service._convert_to_response(call)


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
    logger.info(f"WebSocket connection attempt with token: {token[:20]}...")
    
    # Authenticate user
    try:
        from auth.utils.jwt_token import JWTUtils
        from auth.repositories.user_repository import user_repository
        jwt_utils = JWTUtils()
        payload = jwt_utils.verify_token(token)
        
        if not payload:
            logger.error("Invalid or expired token")
            await websocket.accept()
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        logger.warning(f"[WS_AUTH] Token payload: {payload}")
        
        # Get user_id from token or lookup by email
        user_id = payload.get("user_id")
        logger.warning(f"[WS_AUTH] user_id from token: {user_id}")
        
        if not user_id:
            # Token has email in 'sub', need to look up user_id
            email = payload.get("sub")
            logger.warning(f"[WS_AUTH] Looking up user by email: {email}")
            if email:
                # Get database session
                from database import SessionLocal
                db = SessionLocal()
                try:
                    user = user_repository.get_by_email(db, email)
                    if user:
                        user_id = user.id
                        logger.warning(f"[WS_AUTH] Found user_id from database: {user_id} (type: {type(user_id).__name__})")
                    else:
                        logger.error(f"[WS_AUTH] User not found for email: {email}")
                finally:
                    db.close()
        
        if not user_id:
            logger.error("Could not determine user_id from token")
            await websocket.accept()
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
            
        # Convert to string for consistency
        user_id = str(user_id)
        logger.warning(f"[WS_AUTH] ✓ User authenticated: {user_id} (type: {type(user_id).__name__})")
        
    except Exception as e:
        logger.error(f"WebSocket authentication failed: {e}", exc_info=True)
        try:
            await websocket.accept()
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        except:
            pass
        return
    
    # Connect user with their info from token
    user_info = {
        "email": payload.get("sub", ""),
        "username": payload.get("username", ""),
        "user_id": user_id
    }
    
    # If username not in token, fetch from database
    if not user_info.get("username"):
        from auth.repositories.user_repository import user_repository
        from database import SessionLocal
        db = SessionLocal()
        try:
            user = user_repository.get(db, int(user_id) if isinstance(user_id, str) else user_id)
            if user:
                user_info["username"] = user.username
                logger.warning(f"[WS_AUTH] Fetched username from DB: {user.username}")
        finally:
            db.close()
    
    # Fallback username if still empty
    if not user_info.get("username"):
        user_info["username"] = payload.get("sub", "User").split("@")[0]  # Use email prefix
    
    await call_signaling_manager.connect(websocket, user_id, user_info)
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_json()
            message_type = data.get("type")
            message_data = data.get("data", {})
            
            logger.info(f"Received WebSocket message from {user_id}: {message_type}")
            
            # Handle different message types (support both uppercase and lowercase)
            msg_type_lower = message_type.lower() if message_type else ""
            
            if msg_type_lower == WSMessageType.WEBRTC_OFFER.value:
                # Forward WebRTC offer to target peer
                to_user_id = message_data.get("to_user_id")
                if to_user_id:
                    await call_signaling_manager.send_webrtc_signal(
                        from_user_id=user_id,
                        to_user_id=to_user_id,
                        signal_type=WSMessageType.WEBRTC_OFFER.value,
                        data=message_data.get("offer")
                    )
            
            elif msg_type_lower == WSMessageType.WEBRTC_ANSWER.value:
                # Forward WebRTC answer to target peer
                to_user_id = message_data.get("to_user_id")
                if to_user_id:
                    await call_signaling_manager.send_webrtc_signal(
                        from_user_id=user_id,
                        to_user_id=to_user_id,
                        signal_type=WSMessageType.WEBRTC_ANSWER.value,
                        data=message_data.get("answer")
                    )
            
            elif msg_type_lower == WSMessageType.WEBRTC_ICE_CANDIDATE.value:
                # Forward ICE candidate to target peer
                to_user_id = message_data.get("to_user_id")
                if to_user_id:
                    await call_signaling_manager.send_webrtc_signal(
                        from_user_id=user_id,
                        to_user_id=to_user_id,
                        signal_type=WSMessageType.WEBRTC_ICE_CANDIDATE.value,
                        data=message_data.get("candidate")
                    )

            elif msg_type_lower in ("call_accepted",):
                # Callee accepted the call
                to_user_id = message_data.get("to_user_id")
                call_id = message_data.get("call_id")
                
                if call_id:
                    # Add accepter to signaling manager
                    call_signaling_manager.add_to_call(call_id, user_id)
                    
                    # Get existing participants in the call
                    existing = call_signaling_manager.get_call_participants(call_id)
                    existing_list = [uid for uid in existing if uid != user_id]
                    
                    # Notify existing participants → they will create offers to new user
                    for pid in existing_list:
                        await call_signaling_manager.send_to_user(pid, {
                            "type": "PARTICIPANT_JOINED",
                            "data": {
                                "call_id": call_id,
                                "user_id": user_id
                            }
                        })
                
                # Also forward CALL_ACCEPTED for UI update
                if to_user_id:
                    await call_signaling_manager.send_to_user(to_user_id, {
                        "type": "CALL_ACCEPTED",
                        "from_user_id": user_id,
                        "data": message_data
                    })

            elif msg_type_lower in ("call_declined",):
                # Callee declined → forward to caller
                to_user_id = message_data.get("to_user_id")
                if to_user_id:
                    await call_signaling_manager.send_to_user(to_user_id, {
                        "type": "CALL_DECLINED",
                        "from_user_id": user_id,
                        "data": message_data
                    })

            elif msg_type_lower in ("call_ended",):
                # User leaving / ending call
                call_id = message_data.get("call_id")
                to_user_id = message_data.get("to_user_id")
                
                if call_id:
                    # Remove from signaling manager
                    call_signaling_manager.remove_from_call(call_id, user_id)
                    remaining = call_signaling_manager.get_call_participants(call_id)
                    
                    if len(remaining) <= 1:
                        # Last person or empty → end call for everyone
                        for pid in remaining:
                            await call_signaling_manager.send_to_user(pid, {
                                "type": "CALL_ENDED",
                                "from_user_id": user_id,
                                "data": {"call_id": call_id}
                            })
                        # Clean up
                        if call_id in call_signaling_manager.call_participants:
                            del call_signaling_manager.call_participants[call_id]
                    else:
                        # Group call: notify others this user left
                        for pid in remaining:
                            await call_signaling_manager.send_to_user(pid, {
                                "type": "PARTICIPANT_LEFT",
                                "data": {"call_id": call_id, "user_id": user_id}
                            })
                elif to_user_id:
                    # No call_id, just forward directly (backward compat)
                    await call_signaling_manager.send_to_user(to_user_id, {
                        "type": "CALL_ENDED",
                        "from_user_id": user_id,
                        "data": message_data
                    })

            else:
                logger.warning(f"Unknown message type: {message_type}")
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user_id}")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
    finally:
        # Disconnect user
        call_signaling_manager.disconnect(user_id)
