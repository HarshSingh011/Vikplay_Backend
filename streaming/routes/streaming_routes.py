from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from auth.services import get_user_service
from ..services.streaming_service import StreamingService
from ..schemas.streaming_schemas import StreamStartRequest

router = APIRouter(
    prefix="/api/streaming",
    tags=["streaming"],
)

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    user_service = get_user_service(db)
    result = user_service.get_user_by_token(credentials.credentials)
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result.message,
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {
        "user_id": result.data.id,
        "username": result.data.username,
        "email": result.data.email,
    }


def get_streaming_service(db: Session = Depends(get_db)) -> StreamingService:
    return StreamingService(db)


# ── Start / End ──────────────────────────────────────────


@router.post("/streams/start", response_model=dict)
async def start_stream(
    data: StreamStartRequest,
    current_user: dict = Depends(get_current_user),
    service: StreamingService = Depends(get_streaming_service),
):
    """Create a stream AND immediately go live.
    Accepts title, description (optional) and thumbnail_url (optional).
    Enforces one live stream per user — returns 409 if already streaming."""
    return service.quick_start_stream(current_user["user_id"], data)


@router.post("/streams/end/{stream_code}", response_model=dict)
async def end_stream(
    stream_code: str,
    current_user: dict = Depends(get_current_user),
    service: StreamingService = Depends(get_streaming_service),
):
    """End a live stream by its 6-digit code (owner only)."""
    return service.end_stream_by_code(stream_code, current_user["user_id"])


# ── Discovery & Viewing ─────────────────────────────────


@router.get("/streams/live", response_model=List[dict])
async def get_live_streams(
    service: StreamingService = Depends(get_streaming_service),
):
    """Get all currently live streams."""
    streams = service.get_live_streams()
    return [
        {
            "stream_code": s.stream_code,
            "title": s.title,
            "description": s.description,
            "user_id": s.user_id,
            "viewer_count": s.viewer_count,
            "thumbnail_url": s.thumbnail_url,
            "started_at": s.started_at.isoformat() if s.started_at else None,
        }
        for s in streams
    ]


@router.get("/streams/code/{stream_code}", response_model=dict)
async def get_stream_by_code(
    stream_code: str,
    service: StreamingService = Depends(get_streaming_service),
):
    """Get a specific stream by its 6-digit stream code."""
    result = service.get_stream_by_code(stream_code)
    if not result:
        raise HTTPException(status_code=404, detail="Stream not found")
    return result


@router.get("/streams/search", response_model=List[dict])
async def search_streams(
    q: str = Query(..., min_length=1, description="Search query"),
    live_only: bool = Query(False, description="Only return live streams"),
    service: StreamingService = Depends(get_streaming_service),
):
    """Search streams by title or description."""
    return service.search_streams(q, live_only)


# ── History ──────────────────────────────────────────────


@router.get("/streams/history/me", response_model=List[dict])
async def get_my_stream_history(
    current_user: dict = Depends(get_current_user),
    service: StreamingService = Depends(get_streaming_service),
):
    """All past streams for the authenticated user with date, time,
    duration, start/end and peak viewers."""
    return service.get_stream_history(current_user["user_id"])


# ── Chat ─────────────────────────────────────────────────


@router.get("/streams/code/{stream_code}/chat", response_model=List[dict])
async def get_stream_chat(
    stream_code: str,
    limit: int = Query(100, ge=1, le=500),
    service: StreamingService = Depends(get_streaming_service),
):
    """Get chat messages for a stream using its 6-digit code."""
    return service.get_chat_by_stream_code(stream_code, limit)