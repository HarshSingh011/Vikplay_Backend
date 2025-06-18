import uuid
import json
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from database import get_db
import models.models as models
# Temporarily disable webrtc imports until aiortc is properly installed
# from utils.webrtc import create_broadcaster, create_viewer, get_viewer_count

router = APIRouter(
    prefix="/webrtc",
    tags=["webrtc"]
)

@router.post("/offer")
async def webrtc_offer(
    request: dict,
    db: Session = Depends(get_db)
):
    """Handle WebRTC offer from broadcaster or viewer"""
    
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
    
    # Handle broadcaster or viewer
    if is_broadcaster:
        # Verify stream key
        stream_key = request.get("stream_key")
        if not stream_key or stream.stream_key != stream_key:
            raise HTTPException(status_code=403, detail="Invalid stream key")
        
        # Create broadcaster peer connection
        pc = await create_broadcaster(client_id, stream_id)
        
        # Set stream to live
        stream.is_live = True
        db.commit()
    else:
        # Create viewer peer connection
        broadcaster_id = stream.user_id
        pc = await create_viewer(client_id, broadcaster_id)
        if not pc:
            raise HTTPException(status_code=404, detail="Broadcaster not found")
    
    # Set remote description
    offer = {"sdp": sdp, "type": type}
    await pc.setRemoteDescription(offer)
    
    # Create answer
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)
    
    # Update viewer count
    stream.viewer_count = get_viewer_count(stream.user_id)
    db.commit()
    
    return {
        "sdp": pc.localDescription.sdp,
        "type": pc.localDescription.type,
        "client_id": client_id
    }

@router.post("/ice-candidate")
async def webrtc_ice_candidate(
    request: dict,
    db: Session = Depends(get_db)
):
    """Handle ICE candidate from client"""
    
    client_id = request.get("client_id")
    candidate = request.get("candidate")
    sdpMid = request.get("sdpMid")
    sdpMLineIndex = request.get("sdpMLineIndex")
    
    if not client_id or not candidate:
        raise HTTPException(status_code=400, detail="Missing required fields")
    
    # Find the peer connection
    from utils.webrtc import peer_connections, broadcasters
    
    pc = None
    if client_id in peer_connections:
        pc = peer_connections[client_id]
    elif client_id in broadcasters:
        pc = broadcasters[client_id]["pc"]
    
    if not pc:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    # Add ICE candidate
    ice_candidate = {"candidate": candidate, "sdpMid": sdpMid, "sdpMLineIndex": sdpMLineIndex}
    await pc.addIceCandidate(ice_candidate)
    
    return {"status": "success"}

@router.post("/end-stream/{stream_id}")
async def end_stream(
    stream_id: int,
    request: dict,
    db: Session = Depends(get_db)
):
    """End a stream"""
    
    stream_key = request.get("stream_key")
    client_id = request.get("client_id")
    
    # Get stream from database
    stream = db.query(models.Stream).filter(models.Stream.id == stream_id).first()
    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")
    
    # Verify stream key
    if not stream_key or stream.stream_key != stream_key:
        raise HTTPException(status_code=403, detail="Invalid stream key")
    
    # Set stream to not live
    stream.is_live = False
    stream.viewer_count = 0
    db.commit()
    
    # Close broadcaster connection
    from utils.webrtc import broadcasters
    if client_id in broadcasters:
        pc = broadcasters[client_id]["pc"]
        await pc.close()
    
    return {"status": "success"}


@router.get("/test", tags=["webrtc"])
async def test_webrtc_service():
    """Test if WebRTC service is functioning properly"""
    try:
        from utils.webrtc import get_active_broadcasters, peer_connections
        from aiortc import RTCPeerConnection
        
        pc = RTCPeerConnection()
        await pc.close()
        
        return {
            "status": "ok",
            "message": "WebRTC service is running",
            "active_broadcasters": len(get_active_broadcasters()),
            "total_connections": len(peer_connections)
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"WebRTC service error: {str(e)}"
        }