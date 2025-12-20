from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
from auth.services import get_user_service
from ..services.streaming_service import StreamingService
from ..utils.webrtc_manager import webrtc_manager
from ..schemas.webrtc_schemas import StreamSessionInfo
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/webrtc",
    tags=["webrtc"]
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

@router.get("/session/{stream_id}", response_model=dict)
async def get_stream_session(
    stream_id: int,
    service: StreamingService = Depends(get_streaming_service)
):
    """Get WebRTC session info for a stream"""
    stream = service.get_stream(stream_id)
    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")
    
    viewer_count = webrtc_manager.get_viewer_count(stream_id)
    is_live = stream_id in webrtc_manager.broadcasters
    
    return {
        "stream_id": stream_id,
        "is_live": is_live,
        "viewer_count": viewer_count,
        "stream_info": stream
    }

@router.get("/active-streams", response_model=dict)
async def get_active_webrtc_streams():
    """Get all active WebRTC streams"""
    active_streams = webrtc_manager.get_active_streams()
    return {
        "active_streams": active_streams,
        "total": len(active_streams)
    }

@router.get("/user-stream-status", response_model=dict)
async def check_user_stream_status(
    current_user: dict = Depends(get_current_user)
):
    """Check if user has an active stream"""
    user_id = current_user["user_id"]
    active_stream_id = webrtc_manager.is_user_streaming(user_id)
    
    return {
        "has_active_stream": active_stream_id is not None,
        "stream_id": active_stream_id,
        "user_id": user_id
    }

# TEST MODE WebSocket endpoints (no authentication required for testing)
@router.websocket("/ws/test/broadcast/{stream_id}")
async def webrtc_test_broadcast_websocket(
    websocket: WebSocket,
    stream_id: int
):
    """TEST MODE: WebSocket endpoint for broadcaster (no auth required)"""
    
    # Use stream_id as user_id for testing
    user_id = stream_id * 1000
    
    logger.info(f"TEST MODE: Broadcaster connecting - stream_id={stream_id}, user_id={user_id}")
    
    # Connect broadcaster
    result = await webrtc_manager.connect_broadcaster(websocket, stream_id, user_id)
    
    if not result["success"]:
        return
    
    try:
        while True:
            # Receive WebRTC signaling messages
            data = await websocket.receive_json()
            
            # Handle different message types
            message_type = data.get("type")
            
            if message_type == "answer":
                await webrtc_manager.handle_signal(websocket, data)
            
            elif message_type == "ice_candidate":
                await webrtc_manager.handle_signal(websocket, data)
            
            elif message_type == "ping":
                await websocket.send_json({"type": "pong"})
            
            else:
                logger.warning(f"Unknown message type from broadcaster: {message_type}")
    
    except WebSocketDisconnect:
        logger.info(f"TEST MODE: Broadcaster WebSocket disconnected: stream_id={stream_id}")
    except Exception as e:
        logger.error(f"TEST MODE: Broadcaster WebSocket error: {e}")
    finally:
        webrtc_manager.disconnect(websocket)

@router.websocket("/ws/test/view/{stream_id}")
async def webrtc_test_view_websocket(
    websocket: WebSocket,
    stream_id: int
):
    """TEST MODE: WebSocket endpoint for viewer (no auth required)"""
    
    # Generate random user_id for testing
    user_id = hash(websocket) % 1000000
    
    logger.info(f"TEST MODE: Viewer connecting - stream_id={stream_id}, user_id={user_id}")
    
    # Connect viewer
    result = await webrtc_manager.connect_viewer(websocket, stream_id, user_id)
    
    if not result["success"]:
        return
    
    try:
        while True:
            # Receive WebRTC signaling messages
            data = await websocket.receive_json()
            
            # Handle different message types
            message_type = data.get("type")
            
            if message_type == "offer":
                await webrtc_manager.handle_signal(websocket, data)
            
            elif message_type == "ice_candidate":
                await webrtc_manager.handle_signal(websocket, data)
            
            elif message_type == "ping":
                await websocket.send_json({"type": "pong"})
            
            else:
                logger.warning(f"Unknown message type from viewer: {message_type}")
    
    except WebSocketDisconnect:
        logger.info(f"TEST MODE: Viewer WebSocket disconnected: stream_id={stream_id}, user_id={user_id}")
    except Exception as e:
        logger.error(f"TEST MODE: Viewer WebSocket error: {e}")
    finally:
        webrtc_manager.disconnect(websocket)

# WebSocket endpoint for WebRTC signaling - Broadcaster
@router.websocket("/ws/broadcast/{stream_id}")
async def webrtc_broadcast_websocket(
    websocket: WebSocket,
    stream_id: int,
    token: str,
    db: Session = Depends(get_db)
):
    """WebSocket endpoint for broadcaster to stream via WebRTC"""
    
    # Accept WebSocket connection FIRST
    await websocket.accept()
    logger.info(f"Broadcaster WebSocket accepted for stream_id={stream_id}")
    
    # Authenticate user from token
    try:
        logger.info(f"Authenticating broadcaster with token: {token[:20]}...")
        user_service = get_user_service(db)
        result = user_service.get_user_by_token(token)
        
        if not result.success:
            logger.error(f"Authentication failed: {result.message}")
            await websocket.close(code=4003, reason=f"Authentication failed: {result.message}")
            return
        
        user_id = result.data.id
        logger.info(f"✅ Authenticated broadcaster: user_id={user_id}, stream_id={stream_id}")
    except Exception as e:
        logger.error(f"Authentication exception: {e}", exc_info=True)
        await websocket.close(code=4003, reason="Authentication failed")
        return
    
    # Get or create stream (optional database tracking)
    service = StreamingService(db)
    try:
        stream = service.get_stream(stream_id)
        
        # If stream exists, verify ownership
        if stream and stream["stream"].user_id != user_id:
            logger.warning(f"Stream {stream_id} belongs to another user")
            await websocket.close(code=4005, reason="Not authorized")
            return
        
        # Mark stream as live if it exists
        if stream:
            service.start_stream(stream_id, user_id)
    except Exception as e:
        # Stream doesn't exist in DB - that's OK, WebRTC will still work
        logger.info(f"Stream {stream_id} not in database, proceeding with WebRTC only: {e}")
    
    # Connect broadcaster (this works without DB stream)
    logger.info(f"Connecting broadcaster - stream_id={stream_id}, user_id={user_id}")
    result = await webrtc_manager.connect_broadcaster(websocket, stream_id, user_id, skip_accept=True)
    
    if not result["success"]:
        return  # Already closed in connect_broadcaster
    
    try:
        while True:
            # Receive WebRTC signaling messages
            data = await websocket.receive_json()
            
            # Handle different message types
            message_type = data.get("type")
            
            if message_type == "answer":
                # Broadcaster sending answer to a viewer
                await webrtc_manager.handle_signal(websocket, data)
            
            elif message_type == "ice_candidate":
                # ICE candidate from broadcaster
                await webrtc_manager.handle_signal(websocket, data)
            
            elif message_type == "ping":
                # Keep-alive ping
                await websocket.send_json({"type": "pong"})
            
            else:
                logger.warning(f"Unknown message type from broadcaster: {message_type}")
    
    except WebSocketDisconnect:
        logger.info(f"Broadcaster WebSocket disconnected: stream_id={stream_id}")
    except Exception as e:
        logger.error(f"Broadcaster WebSocket error: {e}")
    finally:
        # Disconnect and cleanup
        webrtc_manager.disconnect(websocket)
        
        # Mark stream as offline in database
        try:
            service.end_stream(stream_id, user_id)
        except Exception as e:
            logger.warning(f"Could not mark stream as offline: {e}")

# WebSocket endpoint for WebRTC signaling - Viewer
@router.websocket("/ws/view/{stream_id}")
async def webrtc_view_websocket(
    websocket: WebSocket,
    stream_id: int,
    token: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """WebSocket endpoint for viewer to watch WebRTC stream"""
    
    # Accept WebSocket connection FIRST
    await websocket.accept()
    
    # Authenticate user (optional for viewers, but recommended)
    user_id = None
    if token:
        try:
            user_service = get_user_service(db)
            result = user_service.get_user_by_token(token)
            
            if result.success:
                user_id = result.data.id
                logger.info(f"Authenticated viewer: user_id={user_id}")
            else:
                # Allow anonymous viewing
                user_id = hash(websocket) % 1000000
                logger.info(f"Anonymous viewer (auth failed): user_id={user_id}")
        except Exception as e:
            user_id = hash(websocket) % 1000000
            logger.info(f"Anonymous viewer (exception): user_id={user_id}")
    else:
        # Anonymous viewer
        user_id = hash(websocket) % 1000000
        logger.info(f"Anonymous viewer (no token): user_id={user_id}")
    
    # Check if stream exists in DB (optional)
    service = StreamingService(db)
    try:
        stream = service.get_stream(stream_id)
        if stream:
            logger.info(f"Stream {stream_id} found in database")
    except Exception as e:
        # Stream doesn't exist in DB - that's OK, WebRTC will still work if broadcaster is connected
        logger.info(f"Stream {stream_id} not in database, proceeding with WebRTC only: {e}")
    
    # Connect viewer (works without DB stream if broadcaster is connected)
    logger.info(f"Connecting viewer - stream_id={stream_id}, user_id={user_id}")
    result = await webrtc_manager.connect_viewer(websocket, stream_id, user_id, skip_accept=True)
    
    if not result["success"]:
        return  # Already handled in connect_viewer
    
    try:
        while True:
            # Receive WebRTC signaling messages
            data = await websocket.receive_json()
            
            # Handle different message types
            message_type = data.get("type")
            
            if message_type == "offer":
                # Viewer sending offer to broadcaster
                await webrtc_manager.handle_signal(websocket, data)
            
            elif message_type == "ice_candidate":
                # ICE candidate from viewer
                await webrtc_manager.handle_signal(websocket, data)
            
            elif message_type == "ping":
                # Keep-alive ping
                await websocket.send_json({"type": "pong"})
            
            else:
                logger.warning(f"Unknown message type from viewer: {message_type}")
    
    except WebSocketDisconnect:
        logger.info(f"Viewer WebSocket disconnected: stream_id={stream_id}, user_id={user_id}")
    except Exception as e:
        logger.error(f"Viewer WebSocket error: {e}")
    finally:
        # Disconnect and cleanup
        webrtc_manager.disconnect(websocket)
