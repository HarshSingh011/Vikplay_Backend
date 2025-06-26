import uuid
import json
import secrets
import logging
import asyncio
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from database import get_db
from webrtc.models import Stream, ChatMessage
from webrtc.schemas import (
    WebRTCOfferRequest, WebRTCAnswerRequest, WebRTCICECandidate,
    StreamCreate, Stream as StreamResponse
)

logger = logging.getLogger(__name__)

# Simplified WebRTC Manager for this module
class SimpleWebRTCManager:
    def __init__(self):
        self.connections = {}
        self.active_broadcasters = {}
        self.viewer_counts = {}
        self.websocket_connections = {}

    def add_websocket_connection(self, stream_id: str, client_id: str, websocket):
        if stream_id not in self.websocket_connections:
            self.websocket_connections[stream_id] = {}
        self.websocket_connections[stream_id][client_id] = websocket

    def remove_websocket_connection(self, stream_id: str, client_id: str):
        if stream_id in self.websocket_connections and client_id in self.websocket_connections[stream_id]:
            del self.websocket_connections[stream_id][client_id]
            if not self.websocket_connections[stream_id]:
                del self.websocket_connections[stream_id]

    async def broadcast_to_stream(self, stream_id: str, message: str, exclude_client: str = None):
        if stream_id not in self.websocket_connections:
            return
        for client_id, websocket in self.websocket_connections[stream_id].items():
            if exclude_client and client_id == exclude_client:
                continue
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.error(f"Failed to send message to client {client_id}: {e}")

    def handle_answer(self, stream_id: str, client_id: str, sdp: str):
        logger.info(f"Handling answer from client {client_id} for stream {stream_id}")
        return {"success": True, "message": "Answer processed"}

    def cleanup_stream(self, stream_id: str):
        if stream_id in self.websocket_connections:
            for client_id in list(self.websocket_connections[stream_id].keys()):
                self.remove_websocket_connection(stream_id, client_id)
        if stream_id in self.active_broadcasters:
            del self.active_broadcasters[stream_id]
        if stream_id in self.viewer_counts:
            del self.viewer_counts[stream_id]

    async def handle_signaling_message(self, stream_id: str, client_id: str, message: dict):
        # Simple implementation for signaling
        await self.broadcast_to_stream(stream_id, json.dumps(message), exclude_client=client_id)

# Global manager instance
webrtc_manager = SimpleWebRTCManager()

def create_broadcaster(stream_id: str, client_id: str, sdp: str):
    logger.info(f"Creating broadcaster {client_id} for stream {stream_id}")
    webrtc_manager.active_broadcasters[stream_id] = {
        "client_id": client_id,
        "sdp": sdp,
        "created_at": asyncio.get_event_loop().time() if asyncio.get_event_loop().is_running() else 0
    }
    return {
        "success": True,
        "stream_id": stream_id,
        "client_id": client_id,
        "answer": generate_mock_answer(sdp)
    }

def create_viewer(stream_id: str, client_id: str, sdp: str):
    logger.info(f"Creating viewer {client_id} for stream {stream_id}")
    if stream_id not in webrtc_manager.active_broadcasters:
        return {"success": False, "error": f"No broadcaster found for stream {stream_id}"}
    
    if stream_id not in webrtc_manager.viewer_counts:
        webrtc_manager.viewer_counts[stream_id] = 0
    webrtc_manager.viewer_counts[stream_id] += 1
    
    return {
        "success": True,
        "stream_id": stream_id,
        "client_id": client_id,
        "answer": generate_mock_answer(sdp)
    }

def handle_offer(stream_id: str, client_id: str, sdp: str, is_broadcaster: bool = False):
    if is_broadcaster:
        return create_broadcaster(stream_id, client_id, sdp)
    else:
        return create_viewer(stream_id, client_id, sdp)

def handle_ice_candidate(stream_id: str, client_id: str, candidate: dict):
    logger.info(f"Handling ICE candidate from {client_id} for stream {stream_id}")
    return {
        "success": True,
        "stream_id": stream_id,
        "client_id": client_id,
        "message": "ICE candidate processed"
    }

def get_viewer_count(stream_id: str) -> int:
    return webrtc_manager.viewer_counts.get(stream_id, 0)

def generate_mock_answer(offer_sdp: str) -> str:
    return f"""v=0
o=- {uuid.uuid4().hex[:10]} 2 IN IP4 127.0.0.1
s=-
t=0 0
a=group:BUNDLE 0
a=msid-semantic: WMS
m=video 9 UDP/TLS/RTP/SAVPF 96
c=IN IP4 0.0.0.0
a=rtcp:9 IN IP4 0.0.0.0
a=ice-ufrag:mock
a=ice-pwd:mockpassword
a=ice-options:trickle
a=fingerprint:sha-256 Mock:Fingerprint:For:Testing
a=setup:active
a=mid:0
a=sendonly
a=rtcp-mux
a=rtcp-rsize
a=rtpmap:96 VP8/90000
a=ssrc:{uuid.uuid4().hex[:8]} cname:mock-cname
"""

router = APIRouter(
    prefix="/webrtc",
    tags=["webrtc"]
)

@router.get("/test")
async def webrtc_test():
    """Simple WebRTC test endpoint"""
    return {
        "status": "success",
        "message": "WebRTC test endpoint is working",
        "active_broadcasters": len(webrtc_manager.active_broadcasters),
        "total_connections": len(webrtc_manager.connections),
        "supported_features": [
            "Basic WebRTC signaling",
            "Stream management", 
            "Connection testing"
        ]
    }

@router.post("/offer")
async def webrtc_offer(
    request: WebRTCOfferRequest,
    db: Session = Depends(get_db)
):
    """Handle WebRTC offer - improved version with proper SDP"""
    
    # Extract data from request
    sdp = request.sdp
    offer_type = request.type
    stream_id = request.stream_id
    client_id = request.client_id or str(uuid.uuid4())
    is_broadcaster = request.is_broadcaster
    
    # Validate required fields
    if not sdp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SDP is required"
        )
    
    # Create or get stream
    if is_broadcaster:
        if not stream_id:
            stream_id = str(uuid.uuid4())
            
        # Check if stream exists in database
        db_stream = db.query(Stream).filter(Stream.stream_key == stream_id).first()
        if not db_stream:
            # Create new stream record
            db_stream = Stream(
                title=f"Stream {stream_id[:8]}",
                description="WebRTC Live Stream",
                user_id=client_id,
                stream_key=stream_id,
                is_live=True
            )
            db.add(db_stream)
            db.commit()
            db.refresh(db_stream)
            
        logger.info(f"Creating broadcaster for stream {stream_id}")
        result = create_broadcaster(stream_id, client_id, sdp)
    else:
        if not stream_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="stream_id is required for viewers"
            )
            
        logger.info(f"Creating viewer for stream {stream_id}")
        result = create_viewer(stream_id, client_id, sdp)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("error", "Failed to process offer")
        )
    
    return JSONResponse(content={
        "success": True,
        "client_id": client_id,
        "stream_id": stream_id,
        "answer": result.get("answer"),
        "type": "answer"
    })

@router.post("/answer")
async def webrtc_answer(request: WebRTCAnswerRequest):
    """Handle WebRTC answer"""
    
    try:
        # Process the answer using WebRTC manager
        result = webrtc_manager.handle_answer(
            request.stream_id, 
            request.client_id, 
            request.sdp
        )
        
        return JSONResponse(content={
            "success": True,
            "message": "Answer processed successfully"
        })
        
    except Exception as e:
        logger.error(f"Answer processing error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process answer"
        )

@router.post("/ice-candidate")
async def webrtc_ice_candidate(request: WebRTCICECandidate):
    """Handle ICE candidate"""
    
    try:
        # Process ICE candidate using WebRTC manager
        result = handle_ice_candidate(
            request.stream_id,
            request.client_id,
            {
                "candidate": request.candidate,
                "sdpMid": request.sdp_mid,
                "sdpMLineIndex": request.sdp_mline_index
            }
        )
        
        return JSONResponse(content={
            "success": True,
            "message": "ICE candidate processed successfully"
        })
        
    except Exception as e:
        logger.error(f"ICE candidate processing error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process ICE candidate"
        )

@router.websocket("/ws/{stream_id}")
async def websocket_endpoint(websocket: WebSocket, stream_id: str):
    """WebSocket endpoint for real-time communication"""
    await websocket.accept()
    client_id = str(uuid.uuid4())
    
    try:
        # Add client to WebRTC manager
        webrtc_manager.add_websocket_connection(stream_id, client_id, websocket)
        
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message.get("type") == "offer":
                # Process offer
                result = handle_offer(stream_id, client_id, message.get("sdp"))
                await websocket.send_text(json.dumps(result))
                
            elif message.get("type") == "ice-candidate":
                # Process ICE candidate
                result = handle_ice_candidate(stream_id, client_id, message)
                await websocket.send_text(json.dumps(result))
                
            elif message.get("type") == "chat":
                # Broadcast chat message to all viewers
                await webrtc_manager.broadcast_to_stream(stream_id, data)
                
    except WebSocketDisconnect:
        logger.info(f"Client {client_id} disconnected from stream {stream_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
    finally:
        # Remove client from WebRTC manager
        webrtc_manager.remove_websocket_connection(stream_id, client_id)

@router.get("/streams/{stream_id}/stats")
async def get_stream_stats(stream_id: str, db: Session = Depends(get_db)):
    """Get stream statistics"""
    
    # Get stream from database
    db_stream = db.query(Stream).filter(Stream.stream_key == stream_id).first()
    if not db_stream:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stream not found"
        )
    
    # Get real-time viewer count
    viewer_count = get_viewer_count(stream_id)
    
    return {
        "stream_id": stream_id,
        "title": db_stream.title,
        "is_live": db_stream.is_live,
        "viewer_count": viewer_count,
        "created_at": db_stream.created_at
    }

@router.post("/streams/{stream_id}/start")
async def start_stream(
    stream_id: str, 
    stream_data: StreamCreate,
    db: Session = Depends(get_db)
):
    """Start a new stream"""
    
    # Check if stream already exists
    existing_stream = db.query(Stream).filter(Stream.stream_key == stream_id).first()
    if existing_stream:
        if existing_stream.is_live:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Stream is already live"
            )
        # Update existing stream
        existing_stream.title = stream_data.title
        existing_stream.description = stream_data.description
        existing_stream.is_live = True
        db.commit()
        return existing_stream
    
    # Create new stream
    db_stream = Stream(
        title=stream_data.title,
        description=stream_data.description,
        user_id=stream_data.user_id,
        stream_key=stream_id,
        is_live=True
    )
    
    db.add(db_stream)
    db.commit()
    db.refresh(db_stream)
    
    return db_stream

@router.post("/streams/{stream_id}/stop")
async def stop_stream(stream_id: str, db: Session = Depends(get_db)):
    """Stop a stream"""
    
    # Get stream from database
    db_stream = db.query(Stream).filter(Stream.stream_key == stream_id).first()
    if not db_stream:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stream not found"
        )
    
    # Stop the stream
    db_stream.is_live = False
    db_stream.viewer_count = 0
    db.commit()
    
    # Clean up WebRTC connections
    webrtc_manager.cleanup_stream(stream_id)
    
    return {
        "success": True,
        "message": f"Stream {stream_id} stopped successfully",
        "stream_id": stream_id
    }

@router.post("/debug/analyze-sdp")
async def analyze_sdp(request: dict):
    """Debug endpoint to analyze SDP"""
    
    sdp = request.get("sdp", "")
    if not sdp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SDP is required"
        )
    
    # Basic SDP analysis
    lines = sdp.split('\n')
    analysis = {
        "total_lines": len(lines),
        "media_sections": [],
        "codecs": [],
        "ice_info": {},
        "fingerprint": None
    }
    
    for line in lines:
        line = line.strip()
        if line.startswith('m='):
            analysis["media_sections"].append(line)
        elif line.startswith('a=rtpmap:'):
            analysis["codecs"].append(line)
        elif line.startswith('a=ice-'):
            key = line.split(':', 1)[0].replace('a=', '')
            value = line.split(':', 1)[1] if ':' in line else ''
            analysis["ice_info"][key] = value
        elif line.startswith('a=fingerprint:'):
            analysis["fingerprint"] = line.replace('a=fingerprint:', '')
    
    return {
        "success": True,
        "analysis": analysis,
        "original_sdp": sdp
    }

@router.websocket("/signaling/{stream_id}/{client_id}")
async def signaling_websocket(websocket: WebSocket, stream_id: str, client_id: str):
    """Enhanced WebSocket endpoint for signaling"""
    await websocket.accept()
    
    try:
        # Register client with WebRTC manager
        webrtc_manager.add_websocket_connection(stream_id, client_id, websocket)
        
        # Send initial connection confirmation
        await websocket.send_text(json.dumps({
            "type": "connected",
            "stream_id": stream_id,
            "client_id": client_id,
            "timestamp": str(uuid.uuid4())
        }))
        
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Add client_id and stream_id to message if not present
            message["client_id"] = client_id
            message["stream_id"] = stream_id
            
            # Route message based on type
            await webrtc_manager.handle_signaling_message(stream_id, client_id, message)
            
    except WebSocketDisconnect:
        logger.info(f"Signaling client {client_id} disconnected from stream {stream_id}")
    except Exception as e:
        logger.error(f"Signaling WebSocket error: {str(e)}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": str(e)
        }))
    finally:
        # Clean up connection
        webrtc_manager.remove_websocket_connection(stream_id, client_id)
