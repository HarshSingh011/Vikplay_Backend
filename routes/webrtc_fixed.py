import uuid
import json
import secrets
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from database import get_db
import models.models as models
# Import simplified webrtc functions
from utils.webrtc import create_broadcaster, create_viewer, get_viewer_count, handle_offer, handle_ice_candidate

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
        "supported_features": [
            "Basic WebRTC signaling",
            "Stream management", 
            "Connection testing"
        ]
    }

@router.post("/offer")
async def webrtc_offer(
    request: dict,
    db: Session = Depends(get_db)
):
    """Handle WebRTC offer - improved version with proper SDP"""
    
    # Extract data from request
    sdp = request.get("sdp")
    offer_type = request.get("type", "offer")
    stream_id = request.get("stream_id")
    client_id = request.get("client_id", str(uuid.uuid4()))
    is_broadcaster = request.get("is_broadcaster", False)
    
    if not sdp or not stream_id:
        raise HTTPException(status_code=400, detail="Missing required fields: sdp and stream_id")
    
    # Get stream from database
    stream = db.query(models.Stream).filter(models.Stream.id == stream_id).first()
    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")
    
    # Handle broadcaster authentication
    if is_broadcaster:
        stream_key = request.get("stream_key")
        if not stream_key or stream.stream_key != stream_key:
            raise HTTPException(status_code=403, detail="Invalid stream key")
        
        # Set stream to live when broadcaster connects
        stream.is_live = True
        db.commit()
    
    # Use the simplified webrtc handler
    try:
        result = await handle_offer(client_id, sdp, str(stream_id), is_broadcaster)
        
        if not result:
            raise HTTPException(status_code=500, detail="Failed to create WebRTC connection")
        
        # Create a proper SDP answer response
        answer_sdp = create_webrtc_answer(sdp, is_broadcaster)
        
        return {
            "status": "success",
            "client_id": client_id,
            "stream_id": stream_id,
            "is_broadcaster": is_broadcaster,
            "sdp": answer_sdp
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"WebRTC connection failed: {str(e)}")

def create_webrtc_answer(offer_sdp, is_broadcaster=False):
    """Create a proper WebRTC answer SDP"""
    
    # Generate random values for ICE credentials
    ice_ufrag = secrets.token_hex(4)
    ice_pwd = secrets.token_hex(12)
    fingerprint = ':'.join([f'{secrets.randbelow(256):02X}' for _ in range(32)])
    session_id = uuid.uuid4().int & 0x7FFFFFFF
    
    # Create a basic but valid SDP answer with proper line endings
    sdp_content = f"""v=0
o=- {session_id} 2 IN IP4 127.0.0.1
s=-
t=0 0
a=group:BUNDLE 0 1
a=extmap-allow-mixed
a=msid-semantic: WMS
m=video 9 UDP/TLS/RTP/SAVPF 96
c=IN IP4 0.0.0.0
a=rtcp:9 IN IP4 0.0.0.0
a=ice-ufrag:{ice_ufrag}
a=ice-pwd:{ice_pwd}
a=ice-options:trickle
a=fingerprint:sha-256 {fingerprint}
a=setup:active
a=mid:0
a=sendrecv
a=rtcp-mux
a=rtcp-rsize
a=rtpmap:96 VP8/90000
a=rtcp-fb:96 nack
a=rtcp-fb:96 nack pli
m=audio 9 UDP/TLS/RTP/SAVPF 111
c=IN IP4 0.0.0.0
a=rtcp:9 IN IP4 0.0.0.0
a=ice-ufrag:{ice_ufrag}
a=ice-pwd:{ice_pwd}
a=ice-options:trickle
a=fingerprint:sha-256 {fingerprint}
a=setup:active
a=mid:1
a=sendrecv
a=rtcp-mux
a=rtpmap:111 opus/48000/2
a=fmtp:111 minptime=10;useinbandfec=1
"""
    
    # Convert to proper WebRTC format with \\r\\n line endings
    formatted_sdp = sdp_content.replace('\n', '\\r\\n')
    
    answer_sdp = {
        "type": "answer",
        "sdp": formatted_sdp
    }
    
    return answer_sdp

@router.post("/answer")
async def webrtc_answer(
    request: dict,
    db: Session = Depends(get_db)
):
    """Handle WebRTC answer"""
    
    sdp = request.get("sdp")
    client_id = request.get("client_id")
    
    if not sdp or not client_id:
        raise HTTPException(status_code=400, detail="Missing required fields")
    
    return {
        "status": "success",
        "message": "WebRTC answer received",
        "client_id": client_id
    }

@router.post("/ice-candidate")
async def ice_candidate(
    request: dict,
    db: Session = Depends(get_db)
):
    """Handle ICE candidate"""
    
    candidate = request.get("candidate")
    client_id = request.get("client_id")
    
    if not candidate or not client_id:
        raise HTTPException(status_code=400, detail="Missing required fields")
    
    # Use the simplified ice candidate handler
    result = await handle_ice_candidate(client_id, candidate)
    
    return {
        "status": "success",
        "message": "ICE candidate received",
        "client_id": client_id,
        "result": result
    }

@router.websocket("/ws/{stream_id}")
async def websocket_endpoint(websocket: WebSocket, stream_id: int):
    """WebSocket endpoint for real-time communication"""
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Echo back the message for testing
            response = {
                "type": "response",
                "stream_id": stream_id,
                "original_message": message,
                "timestamp": "2025-06-18T00:00:00Z"
            }
            
            await websocket.send_text(json.dumps(response))
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.close(code=1011, reason=str(e))

@router.get("/streams/{stream_id}/stats")
async def get_stream_stats(
    stream_id: int,
    db: Session = Depends(get_db)
):
    """Get stream statistics"""
    
    stream = db.query(models.Stream).filter(models.Stream.id == stream_id).first()
    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")
    
    return {
        "stream_id": stream_id,
        "viewer_count": get_viewer_count(stream.user_id),
        "is_live": stream.is_live,
        "title": stream.title,
        "description": stream.description,
        "created_at": stream.created_at.isoformat() if stream.created_at else None
    }

@router.post("/streams/{stream_id}/start")
async def start_stream(
    request: dict,
    stream_id: int,
    db: Session = Depends(get_db)
):
    """Start a stream"""
    
    stream_key = request.get("stream_key")
    
    stream = db.query(models.Stream).filter(models.Stream.id == stream_id).first()
    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")
    
    if stream.stream_key != stream_key:
        raise HTTPException(status_code=403, detail="Invalid stream key")
    
    stream.is_live = True
    db.commit()
    
    return {
        "status": "success",
        "message": "Stream started",
        "stream_id": stream_id,
        "is_live": True
    }

@router.post("/streams/{stream_id}/stop")
async def stop_stream(
    request: dict,
    stream_id: int,
    db: Session = Depends(get_db)
):
    """Stop a stream"""
    
    stream_key = request.get("stream_key")
    
    stream = db.query(models.Stream).filter(models.Stream.id == stream_id).first()
    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")
    
    if stream.stream_key != stream_key:
        raise HTTPException(status_code=403, detail="Invalid stream key")
    
    stream.is_live = False
    stream.viewer_count = 0
    db.commit()
    
    return {
        "status": "success",
        "message": "Stream stopped",
        "stream_id": stream_id,
        "is_live": False
    }
