"""
Video Session Routes - Session management and tracking
Handles user session tracking for behavioral analysis
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from database import get_db
from auth.utils.jwt_token import verify_token_from_body
from video.services.video_service import SessionService
from video.repositories.video_repository import UserSessionRepository
from video.schemas.video_schemas import (
    SessionStart, SessionActivity, SessionEnd,
    SessionStartWithAuth, SessionActivityWithAuth, SessionEndWithAuth
)
from video.utils import extract_device_info

router = APIRouter(prefix="/session", tags=["session"])

# ====== DEPENDENCY INJECTION ======

def get_session_service(db: Session = Depends(get_db)) -> SessionService:
    """Dependency injection for SessionService"""
    session_repo = UserSessionRepository(db)
    return SessionService(session_repo)

# ====== SESSION ENDPOINTS ======

@router.post("/start")
async def start_session(
    session_data: SessionStartWithAuth,
    request: Request,
    db: Session = Depends(get_db),
    session_service: SessionService = Depends(get_session_service)
):
    """
    AUTOMATIC COLLECTION: Session Patterns
    Authentication via access_token in request body
    """
    # Verify token from body
    current_user = verify_token_from_body(session_data, db)
    
    # Extract device info
    device_info = extract_device_info(request)
    
    return await session_service.start_session(
        user_id=current_user["user_id"],
        session_id=session_data.session_id,
        device_info=device_info
    )


@router.put("/activity")
async def update_session_activity(
    activity_data: SessionActivityWithAuth,
    db: Session = Depends(get_db),
    session_service: SessionService = Depends(get_session_service)
):
    """
    AUTOMATIC COLLECTION: Session Activity
    Authentication via access_token in request body
    """
    # Verify token from body
    current_user = verify_token_from_body(activity_data, db)
    
    # Remove access_token from activity data
    activity_update = activity_data.model_dump(exclude={'access_token'})
    
    return await session_service.update_session_activity(
        user_id=current_user["user_id"],
        session_id=activity_update["session_id"],
        activity_data=activity_update
    )


@router.post("/end")
async def end_session(
    session_data: SessionEndWithAuth,
    db: Session = Depends(get_db),
    session_service: SessionService = Depends(get_session_service)
):
    """
    AUTOMATIC COLLECTION: Session End
    Authentication via access_token in request body
    """
    # Verify token from body
    current_user = verify_token_from_body(session_data, db)
    
    return await session_service.end_session(
        user_id=current_user["user_id"],
        session_id=session_data.session_id,
        session_duration=session_data.session_duration
    )
