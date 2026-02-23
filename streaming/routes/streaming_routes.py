from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from auth.services import get_user_service
from ..services.streaming_service import StreamingService
from ..schemas.streaming_schemas import StreamCreate, StreamUpdateRequest, Stream
from ..utils.websocket_manager import stream_ws_manager

router = APIRouter(
    prefix="/api/streaming",
    tags=["streaming"]
)

# Security scheme
security = HTTPBearer()

# Dependency to get current user
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    user_service = get_user_service(db)
    result = user_service.get_user_by_token(credentials.credentials)

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result.message,
            headers={"WWW-Authenticate": "Bearer"}
        )

    return {
        "user_id": result.data.id,
        "username": result.data.username,
        "email": result.data.email
    }

# Dependency to get streaming service
def get_streaming_service(db: Session = Depends(get_db)) -> StreamingService:
    return StreamingService(db)

@router.post("/streams/", response_model=dict)
async def create_stream(
    stream_data: StreamCreate,
    current_user: dict = Depends(get_current_user),
    service: StreamingService = Depends(get_streaming_service)
):
    """Create a new stream for the authenticated user"""
    return service.create_stream(current_user["user_id"], stream_data)

@router.get("/streams/my", response_model=List[dict])
async def get_my_streams(
    current_user: dict = Depends(get_current_user),
    service: StreamingService = Depends(get_streaming_service)
):
    """Get all streams for the authenticated user"""
    return service.get_user_streams(current_user["user_id"])

@router.get("/streams/live", response_model=List[Stream])
async def get_live_streams(
    service: StreamingService = Depends(get_streaming_service)
):
    """Get all currently live streams"""
    return service.get_live_streams()

@router.get("/streams/{stream_id}", response_model=dict)
async def get_stream(
    stream_id: int,
    service: StreamingService = Depends(get_streaming_service)
):
    """Get a specific stream by ID"""
    result = service.get_stream(stream_id)
    if not result:
        raise HTTPException(status_code=404, detail="Stream not found")
    return result

@router.get("/streams/code/{stream_code}", response_model=dict)
async def get_stream_by_code(
    stream_code: str,
    service: StreamingService = Depends(get_streaming_service)
):
    """Get a specific stream by its 6-digit stream code"""
    result = service.get_stream_by_code(stream_code)
    if not result:
        raise HTTPException(status_code=404, detail="Stream not found")
    return result

@router.post("/streams/{stream_id}/chat", response_model=dict)
async def send_chat_message(
    stream_id: int,
    message: str,
    current_user: dict = Depends(get_current_user),
    service: StreamingService = Depends(get_streaming_service)
):
    """Send a chat message to a live stream"""
    return service.add_chat_message(
        stream_id,
        current_user["user_id"],
        current_user["username"],
        message
    )

@router.get("/streams/{stream_id}/chat", response_model=List[dict])
async def get_stream_chat(
    stream_id: int,
    limit: int = 50,
    service: StreamingService = Depends(get_streaming_service)
):
    """Get chat messages for a stream"""
    return service.get_stream_chat(stream_id, limit)

# WebSocket endpoints for real-time features

@router.websocket("/ws/streams/{stream_id}")
async def stream_websocket(
    websocket: WebSocket,
    stream_id: int,
    db: Session = Depends(get_db)
):
    """WebSocket endpoint for real-time stream interactions"""
    service = StreamingService(db)

    # Verify stream exists
    stream_result = service.get_stream(stream_id)
    if not stream_result:
        await websocket.close(code=4004)  # Stream not found
        return

    await stream_ws_manager.connect(websocket, stream_id)

    try:
        while True:
            data = await websocket.receive_json()

            message_type = data.get("type")

            if message_type == "chat_message":
                # Handle chat message
                message_text = data.get("message", "").strip()
                if not message_text:
                    continue

                # In a real app, you'd get user from token, but for demo:
                user_id = data.get("user_id", 1)  # This should come from auth
                username = data.get("username", "Anonymous")

                # Add to database
                chat_result = service.add_chat_message(stream_id, user_id, username, message_text)

                # Broadcast to all connected clients
                await stream_ws_manager.broadcast_chat_message(
                    stream_id,
                    chat_result["chat_message"].__dict__
                )

            elif message_type == "ping":
                # Respond to ping
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        stream_ws_manager.disconnect(websocket, stream_id)
    except Exception as e:
        stream_ws_manager.disconnect(websocket, stream_id)
        print(f"WebSocket error: {e}")