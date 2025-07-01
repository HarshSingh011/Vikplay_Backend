import uuid
import json
import secrets
import logging
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from database import get_db
import models.models as models
# Import simplified webrtc functions
from utils.webrtc import create_broadcaster, create_viewer, get_viewer_count, handle_offer, handle_ice_candidate

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/webrtc",
    tags=["webrtc"]
)

@router.get("/test")
async def webrtc_test():
    """Simple WebRTC test endpoint"""
    # Import here to avoid circular imports
    from utils.webrtc import webrtc_manager
    
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
        
        # Create a proper SDP answer response using our new dynamic parsing
        answer_sdp = create_webrtc_answer(sdp, is_broadcaster)
        
        return {
            "status": "success",
            "client_id": client_id,
            "stream_id": stream_id,
            "is_broadcaster": is_broadcaster,
            "sdp": answer_sdp
        }
        
    except Exception as e:
        logger.error(f"WebRTC connection error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"WebRTC connection failed: {str(e)}")

def parse_sdp_media_lines(sdp_text):
    """Parse SDP to extract media lines and their properties"""
    lines = sdp_text.split('\r\n') if '\r\n' in sdp_text else sdp_text.split('\n')
    media_sections = []
    current_section = None
    
    for line in lines:
        if line.startswith('m='):
            # Start of a new media section
            if current_section:
                media_sections.append(current_section)
            
            parts = line.split(' ')
            media_type = parts[0][2:]  # Remove 'm='
            port = parts[1]
            protocol = parts[2]
            formats = parts[3:] if len(parts) > 3 else []
            
            current_section = {
                'type': media_type,
                'port': port,
                'protocol': protocol,
                'formats': formats,
                'attributes': [],
                'mid': None
            }
        elif line.startswith('a=') and current_section:
            # Add attribute to current section
            current_section['attributes'].append(line)
            # Extract mid if present
            if line.startswith('a=mid:'):
                current_section['mid'] = line[6:]
    
    # Add the last section
    if current_section:
        media_sections.append(current_section)
    
    return media_sections

def create_webrtc_answer(offer_sdp, is_broadcaster=False):
    """Create a proper WebRTC answer SDP that matches the offer"""
    
    # Generate random values for ICE credentials
    ice_ufrag = secrets.token_hex(4)
    ice_pwd = secrets.token_hex(12)
    fingerprint = ':'.join([f'{secrets.randbelow(256):02X}' for _ in range(32)])
    session_id = uuid.uuid4().int & 0x7FFFFFFF
    
    # Parse the incoming offer to understand its structure
    media_sections = parse_sdp_media_lines(offer_sdp)
    
    # Start building the answer SDP
    answer_lines = [
        "v=0",
        f"o=- {session_id} 2 IN IP4 127.0.0.1",
        "s=-",
        "t=0 0"
    ]
    
    # Add bundle group if we have multiple media sections
    if len(media_sections) > 1:
        mids = [section.get('mid', str(i)) for i, section in enumerate(media_sections) if section.get('mid')]
        if mids:
            answer_lines.append(f"a=group:BUNDLE {' '.join(mids)}")
    
    answer_lines.extend([
        "a=extmap-allow-mixed",
        "a=msid-semantic: WMS"
    ])
    
    # Process each media section from the offer
    for i, section in enumerate(media_sections):
        media_type = section['type']
        formats = section['formats']
        mid = section.get('mid', str(i))
        
        # Create media line with same format as offer
        if formats:
            answer_lines.append(f"m={media_type} 9 {section['protocol']} {' '.join(formats)}")
        else:
            # Fallback for missing formats
            if media_type == 'video':
                answer_lines.append(f"m={media_type} 9 {section['protocol']} 96")
            elif media_type == 'audio':
                answer_lines.append(f"m={media_type} 9 {section['protocol']} 111")
            else:
                answer_lines.append(f"m={media_type} 9 {section['protocol']}")
        
        # Add connection and RTCP info
        answer_lines.extend([
            "c=IN IP4 0.0.0.0",
            "a=rtcp:9 IN IP4 0.0.0.0"
        ])
        
        # Add ICE credentials
        answer_lines.extend([
            f"a=ice-ufrag:{ice_ufrag}",
            f"a=ice-pwd:{ice_pwd}",
            "a=ice-options:trickle"
        ])
        
        # Add DTLS fingerprint
        answer_lines.extend([
            f"a=fingerprint:sha-256 {fingerprint}",
            "a=setup:active"
        ])
        
        # Add mid
        answer_lines.append(f"a=mid:{mid}")
        
        # Add direction attribute
        if is_broadcaster:
            answer_lines.append("a=recvonly")  # Broadcaster receives from viewers
        else:
            answer_lines.append("a=sendrecv")  # Viewers can send and receive
        
        # Add RTCP attributes
        answer_lines.extend([
            "a=rtcp-mux"
        ])
        
        # Add codec-specific attributes based on media type and formats
        if media_type == 'video':
            # Add video codec mappings
            for fmt in formats:
                if fmt == '96':
                    answer_lines.extend([
                        "a=rtpmap:96 VP8/90000",
                        "a=rtcp-fb:96 nack",
                        "a=rtcp-fb:96 nack pli"
                    ])
                elif fmt == '97':
                    answer_lines.extend([
                        "a=rtpmap:97 VP9/90000",
                        "a=rtcp-fb:97 nack",
                        "a=rtcp-fb:97 nack pli"
                    ])
                elif fmt == '98':
                    answer_lines.extend([
                        "a=rtpmap:98 H264/90000",
                        "a=rtcp-fb:98 nack",
                        "a=rtcp-fb:98 nack pli"
                    ])
            
            # Add rtcp-rsize for video
            answer_lines.append("a=rtcp-rsize")
            
        elif media_type == 'audio':
            # Add audio codec mappings
            for fmt in formats:
                if fmt == '111':
                    answer_lines.extend([
                        "a=rtpmap:111 opus/48000/2",
                        "a=fmtp:111 minptime=10;useinbandfec=1"
                    ])
                elif fmt == '103':
                    answer_lines.append("a=rtpmap:103 ISAC/16000")
                elif fmt == '9':
                    answer_lines.append("a=rtpmap:9 G722/8000")
                elif fmt == '0':
                    answer_lines.append("a=rtpmap:0 PCMU/8000")
                elif fmt == '8':
                    answer_lines.append("a=rtpmap:8 PCMA/8000")
    
    # Join all lines with proper WebRTC line endings
    answer_sdp_text = '\r\n'.join(answer_lines) + '\r\n'
    
    answer_sdp = {
        "type": "answer",
        "sdp": answer_sdp_text
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

@router.post("/debug/analyze-sdp")
async def analyze_sdp(request: dict):
    """Debug endpoint to analyze SDP structure"""
    
    sdp = request.get("sdp")
    if not sdp:
        raise HTTPException(status_code=400, detail="Missing SDP")
    
    try:
        # Parse the SDP
        media_sections = parse_sdp_media_lines(sdp)
        
        # Generate a test answer
        test_answer = create_webrtc_answer(sdp, False)
        
        return {
            "status": "success",
            "offer_analysis": {
                "media_sections": media_sections,
                "total_sections": len(media_sections)
            },
            "generated_answer": test_answer,
            "answer_analysis": {
                "media_sections": parse_sdp_media_lines(test_answer["sdp"]),
                "total_sections": len(parse_sdp_media_lines(test_answer["sdp"]))
            }
        }
        
    except Exception as e:
        return {
            "status": "error", 
            "error": str(e),
            "sdp_preview": sdp[:200] + "..." if len(sdp) > 200 else sdp
        }

@router.websocket("/signaling/{stream_id}/{client_id}")
async def websocket_signaling(websocket: WebSocket, stream_id: int, client_id: str):
    """WebSocket endpoint for WebRTC signaling between broadcaster and viewers"""
    await websocket.accept()
    
    # Store the websocket connection
    from utils.webrtc import webrtc_manager
    await webrtc_manager.add_signaling_connection(stream_id, client_id, websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different signaling messages
            message_type = message.get("type")
            
            if message_type == "offer":
                # Forward offer to viewers
                await webrtc_manager.forward_to_viewers(stream_id, client_id, message)
            elif message_type == "answer":
                # Forward answer to broadcaster
                await webrtc_manager.forward_to_broadcaster(stream_id, client_id, message)
            elif message_type == "ice-candidate":
                # Forward ICE candidate to appropriate peer
                await webrtc_manager.forward_ice_candidate(stream_id, client_id, message)
            elif message_type == "viewer-ready":
                # Notify broadcaster that a viewer is ready
                await webrtc_manager.notify_broadcaster_viewer_ready(stream_id, client_id)
            
    except WebSocketDisconnect:
        await webrtc_manager.remove_signaling_connection(stream_id, client_id)
    except Exception as e:
        logger.error(f"WebSocket signaling error: {str(e)}")
        await webrtc_manager.remove_signaling_connection(stream_id, client_id)
