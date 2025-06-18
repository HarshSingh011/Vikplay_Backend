import uuid
import json
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from database import get_db
import models.models as models

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
    """Handle WebRTC offer - simplified version"""
    
    # Extract data from request
    sdp = request.get("sdp")
    type = request.get("type")
    stream_id = request.get("stream_id")
    client_id = request.get("client_id", str(uuid.uuid4()))
    is_broadcaster = request.get("is_broadcaster", False)
    
    if not sdp or not type or not stream_id:
        raise HTTPException(status_code=400, detail="Missing required fields")
    
    # Get stream from database
    stream = db.query(models.Stream).filter(models.Stream.id == stream_id).first()
    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")
    
    # Simplified response for now
    return {
        "status": "success",
        "message": "WebRTC offer received",
        "client_id": client_id,
        "stream_id": stream_id,
        "is_broadcaster": is_broadcaster,
        "sdp": {
            "type": "answer",
            "sdp": "v=0\r\no=- 0 0 IN IP4 127.0.0.1\r\ns=-\r\nt=0 0\r\n"  # Minimal SDP for testing
        }
    }

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
