from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from auth.services import get_user_service
from ..services.streaming_service import StreamingService
from ..schemas.streaming_schemas import (
    StreamStartRequest,
    StreamStartResponse,
    StreamEndResponse,
    LiveStreamItem,
    StreamDetailResponse,
    StreamHistoryItem,
    StreamSearchItem,
    ChatMessageResponse,
)

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


@router.post(
    "/streams/start",
    response_model=StreamStartResponse,
    responses={
        409: {"description": "You already have a live stream running"},
        401: {"description": "Missing or invalid Bearer token"},
    },
)
async def start_stream(
    data: StreamStartRequest,
    current_user: dict = Depends(get_current_user),
    service: StreamingService = Depends(get_streaming_service),
):
    """
    ## Start a new live stream

    Creates a stream record and immediately marks it as **LIVE**.

    **Auth:** Bearer token required (`Authorization: Bearer <token>`).

    **Request body:**
    ```json
    {
      "title": "My Gaming Stream",
      "description": "Playing Minecraft live!",
      "thumbnail_url": "https://example.com/thumb.jpg"
    }
    ```

    **After calling this:**
    - Use the returned `stream_code` to open the broadcaster WebSocket:
      `ws://HOST/api/webrtc/ws/broadcast/{stream_code}?token=<token>`

    **Returns 409** if you already have a live stream running.
    """
    return service.quick_start_stream(current_user["user_id"], data)


@router.post(
    "/streams/end/{stream_code}",
    response_model=StreamEndResponse,
    responses={
        403: {"description": "You are not the owner of this stream"},
        404: {"description": "Stream not found"},
        400: {"description": "Stream is not currently live"},
    },
)
async def end_stream(
    stream_code: str,
    current_user: dict = Depends(get_current_user),
    service: StreamingService = Depends(get_streaming_service),
):
    """
    ## End a live stream

    Stops the stream identified by its 6-digit `stream_code`.
    Only the **owner** (broadcaster) can end the stream.

    **Auth:** Bearer token required.

    **Path param:** `stream_code` — the 6-digit code returned by `/streams/start`.

    **Returns 403** if you are not the owner.
    **Returns 404** if the stream_code does not exist.
    **Returns 400** if the stream is already offline.
    """
    return service.end_stream_by_code(stream_code, current_user["user_id"])


# ── Discovery & Viewing ─────────────────────────────────


@router.get(
    "/streams/live",
    response_model=List[LiveStreamItem],
)
async def get_live_streams(
    service: StreamingService = Depends(get_streaming_service),
):
    """
    ## List all currently live streams

    **No auth required.** Returns every stream that is currently broadcasting.

    Use the returned `stream_code` to:
    - Open a **viewer WebSocket**: `ws://HOST/api/webrtc/ws/view/{stream_code}`
    - Fetch **chat history**: `GET /api/streaming/streams/code/{stream_code}/chat`
    - Get **full stream info**: `GET /api/streaming/streams/code/{stream_code}`
    """
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


@router.get(
    "/streams/code/{stream_code}",
    response_model=StreamDetailResponse,
    responses={
        404: {"description": "Stream not found"},
    },
)
async def get_stream_by_code(
    stream_code: str,
    service: StreamingService = Depends(get_streaming_service),
):
    """
    ## Get stream details by 6-digit code

    **No auth required.**
    Returns the full stream record including `is_live`, `viewer_count`,
    `max_viewer_count`, `started_at`, `ended_at`, and `stream_key`.

    **Returns 404** if stream_code does not exist.
    """
    result = service.get_stream_by_code(stream_code)
    if not result:
        raise HTTPException(status_code=404, detail="Stream not found")
    return result


@router.get(
    "/streams/search",
    response_model=List[StreamSearchItem],
)
async def search_streams(
    q: str = Query(..., min_length=1, description="Search query — matches stream title or description"),
    live_only: bool = Query(False, description="If true, only return currently live streams"),
    service: StreamingService = Depends(get_streaming_service),
):
    """
    ## Search streams by title or description

    **No auth required.**

    **Query params:**
    - `q` *(required)* — search term, matched against title and description
    - `live_only` *(optional, default false)* — set to `true` to only return currently live streams

    **Example:** `/api/streaming/streams/search?q=gaming&live_only=true`
    """
    return service.search_streams(q, live_only)


# ── History ──────────────────────────────────────────────


@router.get(
    "/streams/history/me",
    response_model=List[StreamHistoryItem],
    responses={
        401: {"description": "Missing or invalid Bearer token"},
    },
)
async def get_my_stream_history(
    current_user: dict = Depends(get_current_user),
    service: StreamingService = Depends(get_streaming_service),
):
    """
    ## My past stream history

    **Auth:** Bearer token required.

    Returns all streams you have ever started, including:
    - `started_at` / `ended_at` timestamps
    - `duration_seconds` — total stream length
    - `max_viewer_count` — peak concurrent viewers
    - `is_live` — whether the stream is still active
    """
    return service.get_stream_history(current_user["user_id"])


# ── Chat ─────────────────────────────────────────────────


@router.get(
    "/streams/code/{stream_code}/chat",
    response_model=List[ChatMessageResponse],
    responses={
        404: {"description": "Stream not found"},
    },
)
async def get_stream_chat(
    stream_code: str,
    limit: int = Query(100, ge=1, le=500, description="Number of recent messages to return (1–500)"),
    service: StreamingService = Depends(get_streaming_service),
):
    """
    ## Fetch chat history for a stream

    **No auth required.**
    Returns the most recent `limit` chat messages for the stream.

    **Call this BEFORE opening the viewer WebSocket** to pre-populate
    the chat UI with recent messages.

    **Path param:** `stream_code` — 6-digit public stream code.
    **Query param:** `limit` — how many messages to return (default 100, max 500).

    > ⚠️ This endpoint only **reads** stored messages.
    > To **send** a chat message, use the WebSocket — see the **chat** section in docs.
    > WebSocket URL: `ws://HOST/api/webrtc/ws/view/{stream_code}`
    """
    return service.get_chat_by_stream_code(stream_code, limit)