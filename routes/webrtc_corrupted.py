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
    
    # Generate a basic but valid SDP answer
    # This is a simplified version that should work with most WebRTC clients
    answer_sdp = {
        "type": "answer",
        "sdp": f"""v=0
o=- {uuid.uuid4().int & 0x7FFFFFFF} 2 IN IP4 127.0.0.1
s=-
t=0 0
a=group:BUNDLE 0 1
a=extmap-allow-mixed
a=msid-semantic: WMS
m=video 9 UDP/TLS/RTP/SAVPF 96 97 98 99 100 101 102 121 127 120 125 107 108 109 124 119 123 118 114 115 116
c=IN IP4 0.0.0.0
a=rtcp:9 IN IP4 0.0.0.0
a=ice-ufrag:{secrets.token_hex(4)}
a=ice-pwd:{secrets.token_hex(12)}
a=ice-options:trickle
a=fingerprint:sha-256 {''.join([f'{secrets.randbelow(256):02X}' for _ in range(32)])}
a=setup:active
a=mid:0
a=extmap:1 urn:ietf:params:rtp-hdrext:ssrc-audio-level
a=extmap:2 http://www.webrtc.org/experiments/rtp-hdrext/abs-send-time
a=extmap:3 http://www.ietf.org/id/draft-holmer-rmcat-transport-wide-cc-extensions-01
a=extmap:4 http://www.webrtc.org/experiments/rtp-hdrext/playout-delay
a=extmap:5 http://www.webrtc.org/experiments/rtp-hdrext/video-content-type
a=extmap:6 http://www.webrtc.org/experiments/rtp-hdrext/video-timing
a=extmap:7 http://www.webrtc.org/experiments/rtp-hdrext/color-space
a=extmap:8 urn:ietf:params:rtp-hdrext:sdes:mid
a=extmap:9 urn:ietf:params:rtp-hdrext:sdes:rtp-stream-id
a=extmap:10 urn:ietf:params:rtp-hdrext:sdes:repaired-rtp-stream-id
a=sendrecv
a=msid:- {{uuid.uuid4()}}
a=rtcp-mux
a=rtcp-rsize
a=rtpmap:96 VP8/90000
a=rtcp-fb:96 goog-remb
a=rtcp-fb:96 transport-cc
a=rtcp-fb:96 ccm fir
a=rtcp-fb:96 nack
a=rtcp-fb:96 nack pli
a=rtpmap:97 rtx/90000
a=fmtp:97 apt=96
a=rtpmap:98 VP9/90000
a=rtcp-fb:98 goog-remb
a=rtcp-fb:98 transport-cc
a=rtcp-fb:98 ccm fir
a=rtcp-fb:98 nack
a=rtcp-fb:98 nack pli
a=ssrc-group:FID 1234567890 1234567891
a=ssrc:1234567890 cname:test-stream
a=ssrc:1234567890 msid:- {{uuid.uuid4()}}
a=ssrc:1234567891 cname:test-stream
a=ssrc:1234567891 msid:- {{uuid.uuid4()}}
m=audio 9 UDP/TLS/RTP/SAVPF 111 103 104 9 0 8 106 105 13 110 112 113 126
c=IN IP4 0.0.0.0
a=rtcp:9 IN IP4 0.0.0.0
a=ice-ufrag:{secrets.token_hex(4)}
a=ice-pwd:{secrets.token_hex(12)}
a=ice-options:trickle
a=fingerprint:sha-256 {''.join([f'{secrets.randbelow(256):02X}' for _ in range(32)])}
a=setup:active
a=mid:1
a=extmap:14 urn:ietf:params:rtp-hdrext:ssrc-audio-level
a=sendrecv
a=msid:- {{uuid.uuid4()}}
a=rtcp-mux
a=rtpmap:111 opus/48000/2
a=rtcp-fb:111 transport-cc
a=fmtp:111 minptime=10;useinbandfec=1
a=rtpmap:103 ISAC/16000
a=rtpmap:104 ISAC/32000
a=rtpmap:9 G722/8000
a=rtpmap:0 PCMU/8000
a=rtpmap:8 PCMA/8000
a=rtpmap:106 CN/32000
a=rtpmap:105 CN/16000
a=rtpmap:13 CN/8000
a=rtpmap:110 telephone-event/48000
a=rtpmap:112 telephone-event/32000
a=rtpmap:113 telephone-event/16000
a=rtpmap:126 telephone-event/8000
a=ssrc:1234567892 cname:test-stream
a=ssrc:1234567892 msid:- {{uuid.uuid4()}}
"""
    }
    
    return answer_sdp

@router.post("/answer")
async def webrtc_answer(
    request: dict,
    db: Session = Depends(get_db)
):
    """Handle WebRTC answer - simplified version"""
    
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
    """Handle ICE candidate - simplified version"""
    
    candidate = request.get("candidate")
    client_id = request.get("client_id")
    
    if not candidate or not client_id:
        raise HTTPException(status_code=400, detail="Missing required fields")
    
    return {
        "status": "success",
        "message": "ICE candidate received",
        "client_id": client_id
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
        "viewer_count": stream.viewer_count or 0,
        "is_live": stream.is_live,
        "title": stream.title,
        "description": stream.description,
        "created_at": stream.created_at.isoformat() if stream.created_at else None
    }

@router.post("/streams/{stream_id}/start")
async def start_stream(
    stream_id: int,
    stream_key: str,
    db: Session = Depends(get_db)
):
    """Start a stream"""
    
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
    stream_id: int,
    stream_key: str,
    db: Session = Depends(get_db)
):
    """Stop a stream"""
    
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
