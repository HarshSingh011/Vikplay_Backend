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

@router.get("/session/{stream_code}", response_model=dict)
async def get_stream_session(
    stream_code: str,
    service: StreamingService = Depends(get_streaming_service)
):
    """Get WebRTC session info for a stream"""
    stream = service.get_stream_by_code(stream_code)
    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")
    
    viewer_count = webrtc_manager.get_viewer_count(stream_code)
    is_live = stream_code in webrtc_manager.broadcasters
    
    return {
        "stream_code": stream_code,
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

@router.get("/ice-servers", response_model=dict)
async def get_ice_servers():
    """
    ## Get ICE server configuration (STUN + TURN)

    Returns the ICE server list the Android/web client should pass into
    `RTCPeerConnection`. Call this **once before creating any PeerConnection**.

    Priority order:
    1. If `METERED_API_KEY` + `METERED_APP_NAME` are set → fetches all TURN entries
       live from Metered API (recommended — returns all 4 fallback URLs).
    2. Otherwise falls back to static `TURN_URL` / `TURN_USERNAME` / `TURN_PASSWORD`.
    3. If nothing is set, returns only STUN servers.
    """
    import os
    import httpx

    stun_servers = [
        {"urls": "stun:stun.l.google.com:19302"},
        {"urls": "stun:stun1.l.google.com:19302"},
    ]

    # ── Option 1: Metered dynamic credentials (all 4 TURN URLs) ─────────────
    metered_api_key  = os.getenv("METERED_API_KEY")
    metered_app_name = os.getenv("METERED_APP_NAME")  # e.g. "vikplay.metered.live"

    if metered_api_key and metered_app_name:
        try:
            url = f"https://{metered_app_name}/api/v1/turn/credentials?apiKey={metered_api_key}"
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                metered_servers = resp.json()  # already a list of ICE server objects
                if isinstance(metered_servers, list) and metered_servers:
                    ice_servers = stun_servers + metered_servers
                    return {"ice_servers": ice_servers, "turn_available": True}
        except Exception as e:
            logger.warning(f"Failed to fetch Metered TURN credentials: {e}. Falling back to static env.")

    # ── Option 2: Static env vars ────────────────────────────────────────────
    turn_url      = os.getenv("TURN_URL")
    turn_username = os.getenv("TURN_USERNAME")
    turn_password = os.getenv("TURN_PASSWORD")

    ice_servers = list(stun_servers)
    if turn_url and turn_username and turn_password:
        ice_servers.append({
            "urls":       turn_url,
            "username":   turn_username,
            "credential": turn_password,
        })
        if turn_url.startswith("turn:"):
            turns_url = turn_url.replace("turn:", "turns:", 1)
            ice_servers.append({
                "urls":       turns_url,
                "username":   turn_username,
                "credential": turn_password,
            })

    return {
        "ice_servers": ice_servers,
        "turn_available": bool(turn_url and turn_username and turn_password),
    }

@router.get("/user-stream-status", response_model=dict)
async def check_user_stream_status(
    current_user: dict = Depends(get_current_user)
):
    """Check if user has an active stream"""
    user_id = current_user["user_id"]
    active_stream_code = webrtc_manager.is_user_streaming(user_id)
    
    return {
        "has_active_stream": active_stream_code is not None,
        "stream_code": active_stream_code,
        "user_id": user_id
    }

# TEST MODE WebSocket endpoints (no authentication required for testing)
@router.websocket("/ws/test/broadcast/{stream_code}")
async def webrtc_test_broadcast_websocket(
    websocket: WebSocket,
    stream_code: str
):
    """TEST MODE: WebSocket endpoint for broadcaster (no auth required)"""
    
    # Use hash of stream_code as user_id for testing
    user_id = hash(stream_code) % 1000000
    
    logger.info(f"TEST MODE: Broadcaster connecting - stream_code={stream_code}, user_id={user_id}")
    
    # Connect broadcaster
    result = await webrtc_manager.connect_broadcaster(websocket, stream_code, user_id)
    
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
            
            elif message_type == "chat_message":
                username = data.get("username", "Broadcaster")
                msg_text = data.get("message", "").strip()
                if msg_text:
                    await webrtc_manager.broadcast_chat_message(stream_code, user_id, username, msg_text, role="broadcaster")

            elif message_type == "sync_timestamp":
                broadcaster_ts = data.get("broadcaster_ts", 0)
                await webrtc_manager.relay_sync_timestamp(stream_code, broadcaster_ts)

            elif message_type == "ping":
                await websocket.send_json({"type": "pong"})
            
            else:
                logger.warning(f"Unknown message type from broadcaster: {message_type}")
    
    except WebSocketDisconnect:
        logger.info(f"TEST MODE: Broadcaster WebSocket disconnected: stream_code={stream_code}")
    except Exception as e:
        logger.error(f"TEST MODE: Broadcaster WebSocket error: {e}")
    finally:
        webrtc_manager.disconnect(websocket)

@router.websocket("/ws/test/view/{stream_code}")
async def webrtc_test_view_websocket(
    websocket: WebSocket,
    stream_code: str
):
    """TEST MODE: WebSocket endpoint for viewer (no auth required)"""
    
    # Generate random user_id for testing
    user_id = hash(websocket) % 1000000
    
    logger.info(f"TEST MODE: Viewer connecting - stream_code={stream_code}, user_id={user_id}")
    
    # Connect viewer
    result = await webrtc_manager.connect_viewer(websocket, stream_code, user_id)
    
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
            
            elif message_type == "chat_message":
                username = data.get("username", "Viewer")
                msg_text = data.get("message", "").strip()
                if msg_text:
                    await webrtc_manager.broadcast_chat_message(stream_code, user_id, username, msg_text, role="viewer")

            elif message_type == "request_go_live":
                await webrtc_manager.request_go_live(stream_code, user_id)

            elif message_type == "ping":
                await websocket.send_json({"type": "pong"})
            
            else:
                logger.warning(f"Unknown message type from viewer: {message_type}")
    
    except WebSocketDisconnect:
        logger.info(f"TEST MODE: Viewer WebSocket disconnected: stream_code={stream_code}, user_id={user_id}")
    except Exception as e:
        logger.error(f"TEST MODE: Viewer WebSocket error: {e}")
    finally:
        webrtc_manager.disconnect(websocket)

# WebSocket endpoint for WebRTC signaling - Broadcaster
@router.websocket("/ws/broadcast/{stream_code}")
async def webrtc_broadcast_websocket(
    websocket: WebSocket,
    stream_code: str,
    token: str,
    db: Session = Depends(get_db)
):
    """WebSocket endpoint for broadcaster to stream via WebRTC"""
    
    # Accept WebSocket connection FIRST
    await websocket.accept()
    logger.info(f"Broadcaster WebSocket accepted for stream_code={stream_code}")
    
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
        logger.info(f"Authenticated broadcaster: user_id={user_id}, stream_code={stream_code}")
    except Exception as e:
        logger.error(f"Authentication exception: {e}", exc_info=True)
        await websocket.close(code=4003, reason="Authentication failed")
        return
    
    # Get or create stream (optional database tracking)
    service = StreamingService(db)
    try:
        stream_result = service.get_stream_by_code(stream_code)
        
        # If stream exists, verify ownership
        if stream_result and stream_result["stream"].user_id != user_id:
            logger.warning(f"Stream {stream_code} belongs to another user")
            await websocket.close(code=4005, reason="Not authorized")
            return
        
        # Mark stream as live if it exists
        if stream_result:
            service.start_stream(stream_result["stream"].id, user_id)
    except Exception as e:
        # Stream doesn't exist in DB - that's OK, WebRTC will still work
        logger.info(f"Stream {stream_code} not in database, proceeding with WebRTC only: {e}")
    
    # Connect broadcaster (this works without DB stream)
    logger.info(f"Connecting broadcaster - stream_code={stream_code}, user_id={user_id}")
    result = await webrtc_manager.connect_broadcaster(websocket, stream_code, user_id, skip_accept=True)
    
    if not result["success"]:
        return  # Already closed in connect_broadcaster
    
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
            
            elif message_type == "chat_message":
                username = data.get("username", "Broadcaster")
                msg_text = data.get("message", "").strip()
                if msg_text:
                    await webrtc_manager.broadcast_chat_message(stream_code, user_id, username, msg_text, role="broadcaster")

            elif message_type == "sync_timestamp":
                broadcaster_ts = data.get("broadcaster_ts", 0)
                await webrtc_manager.relay_sync_timestamp(stream_code, broadcaster_ts)

            elif message_type == "ping":
                await websocket.send_json({"type": "pong"})
            
            else:
                logger.warning(f"Unknown message type from broadcaster: {message_type}")
    
    except WebSocketDisconnect:
        logger.info(f"Broadcaster WebSocket disconnected: stream_code={stream_code}")
    except Exception as e:
        logger.error(f"Broadcaster WebSocket error: {e}")
    finally:
        # Read peak viewer count BEFORE disconnect clears it
        peak_viewers = webrtc_manager.get_max_viewer_count(stream_code)
        
        # Disconnect and cleanup
        webrtc_manager.disconnect(websocket)
        
        # Mark stream as offline in database and save peak viewers
        try:
            stream_result = service.get_stream_by_code(stream_code)
            if stream_result:
                stream_obj = stream_result["stream"]
                # Update max_viewer_count if in-memory peak is higher
                if peak_viewers > (stream_obj.max_viewer_count or 0):
                    from ..repositories.streaming_repository import StreamingRepository
                    repo = StreamingRepository(db)
                    repo.update_max_viewers(stream_obj, peak_viewers)
                service.end_stream(stream_obj.id, user_id)
                logger.info(f"Stream {stream_code} ended. Peak viewers: {peak_viewers}")
        except Exception as e:
            logger.warning(f"Could not mark stream as offline: {e}")

# WebSocket endpoint for WebRTC signaling - Viewer
@router.websocket("/ws/view/{stream_code}")
async def webrtc_view_websocket(
    websocket: WebSocket,
    stream_code: str,
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
                user_id = hash(websocket) % 1000000
                logger.info(f"Anonymous viewer (auth failed): user_id={user_id}")
        except Exception as e:
            user_id = hash(websocket) % 1000000
            logger.info(f"Anonymous viewer (exception): user_id={user_id}")
    else:
        user_id = hash(websocket) % 1000000
        logger.info(f"Anonymous viewer (no token): user_id={user_id}")
    
    # Check if stream exists in DB (optional)
    service = StreamingService(db)
    try:
        stream_result = service.get_stream_by_code(stream_code)
        if stream_result:
            logger.info(f"Stream {stream_code} found in database")

            # ── Owner reconnecting as broadcaster via viewer endpoint ──────────
            if stream_result["stream"].user_id == user_id:
                logger.info(f"Owner {user_id} reconnecting as broadcaster via viewer endpoint, stream_code={stream_code}")

                # Evict any stale/dead broadcaster entry for this stream
                webrtc_manager.force_clear_stale_broadcaster(stream_code, user_id)

                # Ensure the stream is marked live in DB
                try:
                    service.start_stream(stream_result["stream"].id, user_id)
                except Exception:
                    pass  # already live is fine

                # Connect as broadcaster (WebSocket already accepted above)
                bc_result = await webrtc_manager.connect_broadcaster(
                    websocket, stream_code, user_id, skip_accept=True
                )
                if not bc_result["success"]:
                    return

                # Notify owner that they are reconnected
                await websocket.send_json({
                    "type": "reconnected",
                    "role": "broadcaster",
                    "stream_code": stream_code,
                    "message": "You have been reconnected to your stream as the broadcaster."
                })

                try:
                    while True:
                        data = await websocket.receive_json()
                        message_type = data.get("type")

                        if message_type == "answer":
                            await webrtc_manager.handle_signal(websocket, data)
                        elif message_type == "ice_candidate":
                            await webrtc_manager.handle_signal(websocket, data)
                        elif message_type == "chat_message":
                            username = data.get("username", "Broadcaster")
                            msg_text = data.get("message", "").strip()
                            if msg_text:
                                await webrtc_manager.broadcast_chat_message(
                                    stream_code, user_id, username, msg_text, role="broadcaster"
                                )
                        elif message_type == "sync_timestamp":
                            await webrtc_manager.relay_sync_timestamp(
                                stream_code, data.get("broadcaster_ts", 0)
                            )
                        elif message_type == "ping":
                            await websocket.send_json({"type": "pong"})
                        else:
                            logger.warning(f"Unknown message type from reconnected broadcaster: {message_type}")

                except WebSocketDisconnect:
                    logger.info(f"Reconnected broadcaster disconnected: stream_code={stream_code}")
                except Exception as e:
                    logger.error(f"Reconnected broadcaster error: {e}")
                finally:
                    peak_viewers = webrtc_manager.get_max_viewer_count(stream_code)
                    webrtc_manager.disconnect(websocket)
                    try:
                        fresh = service.get_stream_by_code(stream_code)
                        if fresh:
                            stream_obj = fresh["stream"]
                            if peak_viewers > (stream_obj.max_viewer_count or 0):
                                from ..repositories.streaming_repository import StreamingRepository
                                repo = StreamingRepository(db)
                                repo.update_max_viewers(stream_obj, peak_viewers)
                            service.end_stream(stream_obj.id, user_id)
                            logger.info(f"Stream {stream_code} ended after broadcaster reconnect/disconnect. Peak viewers: {peak_viewers}")
                    except Exception as e:
                        logger.warning(f"Could not end stream after reconnected broadcaster left: {e}")
                return  # done — skip the viewer path entirely
            # ── End owner reconnection block ───────────────────────────────────

    except Exception as e:
        logger.info(f"Stream {stream_code} not in database, proceeding with WebRTC only: {e}")

    # Connect viewer (works without DB stream if broadcaster is connected)
    logger.info(f"Connecting viewer - stream_code={stream_code}, user_id={user_id}")
    result = await webrtc_manager.connect_viewer(websocket, stream_code, user_id, skip_accept=True)
    
    if not result["success"]:
        return  # Already handled in connect_viewer
    
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
            
            elif message_type == "chat_message":
                username = data.get("username", "Viewer")
                msg_text = data.get("message", "").strip()
                if msg_text:
                    await webrtc_manager.broadcast_chat_message(stream_code, user_id, username, msg_text, role="viewer")

            elif message_type == "request_go_live":
                await webrtc_manager.request_go_live(stream_code, user_id)

            elif message_type == "ping":
                await websocket.send_json({"type": "pong"})
            
            else:
                logger.warning(f"Unknown message type from viewer: {message_type}")
    
    except WebSocketDisconnect:
        logger.info(f"Viewer WebSocket disconnected: stream_code={stream_code}, user_id={user_id}")
    except Exception as e:
        logger.error(f"Viewer WebSocket error: {e}")
    finally:
        # Disconnect and cleanup
        webrtc_manager.disconnect(websocket)
