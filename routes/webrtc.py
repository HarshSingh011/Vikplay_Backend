import uuid
import json
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from database import get_db
import models.models as models
from utils.webrtc import create_broadcaster, create_viewer, get_viewer_count
from aiortc import RTCSessionDescription, RTCIceCandidate

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
        raise HTTPException(status_code=404, detail="Stream not found")    # Handle broadcaster or viewer
    if is_broadcaster:
        # Verify stream key
        stream_key = request.get("stream_key")
        if not stream_key or stream.stream_key != stream_key:
            raise HTTPException(status_code=403, detail="Invalid stream key")
        
        # Use stream.user_id as broadcaster_id for consistency
        broadcaster_id = stream.user_id
        
        # Create broadcaster peer connection
        pc = await create_broadcaster(broadcaster_id, stream_id)
        
        # Store client_id mapping to broadcaster_id
        from utils.webrtc import client_broadcaster_mapping
        client_broadcaster_mapping[client_id] = broadcaster_id
        
        # Set stream to live immediately
        stream.is_live = True
        stream.viewer_count = 0
        db.commit()
        db.refresh(stream)
    else:
        # Create viewer peer connection
        broadcaster_id = stream.user_id
        pc = await create_viewer(client_id, broadcaster_id)
        if not pc:
            raise HTTPException(status_code=404, detail="Broadcaster not found")
        
        # Update viewer count
        stream.viewer_count = get_viewer_count(stream.user_id)
        db.commit()
        db.refresh(stream)
      # Set remote description
    offer_description = RTCSessionDescription(sdp=sdp, type=type)
    await pc.setRemoteDescription(offer_description)
      # Create answer
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)
    
    # Update viewer count for viewers only (broadcaster count is updated above)
    if not is_broadcaster:
        stream.viewer_count = get_viewer_count(stream.user_id)
        db.commit()
        db.refresh(stream)
    
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
    from utils.webrtc import peer_connections, broadcasters, client_broadcaster_mapping
    
    pc = None
    if client_id in peer_connections:
        # This is a viewer
        pc = peer_connections[client_id]
    elif client_id in client_broadcaster_mapping:
        # This is a broadcaster, get the actual broadcaster_id
        broadcaster_id = client_broadcaster_mapping[client_id]
        if broadcaster_id in broadcasters:
            pc = broadcasters[broadcaster_id]["pc"]
    elif client_id in broadcasters:
        # Direct broadcaster access (fallback)
        pc = broadcasters[client_id]["pc"]
    
    if not pc:
        raise HTTPException(status_code=404, detail="Connection not found")
      # Add ICE candidate
    ice_candidate = RTCIceCandidate(
        candidate=candidate,
        sdpMid=sdpMid,
        sdpMLineIndex=sdpMLineIndex
    )
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
    db.refresh(stream)
      # Close broadcaster connection and clean up
    from utils.webrtc import broadcasters, peer_connections, client_broadcaster_mapping
    
    # Find and close broadcaster connection
    broadcaster_found = False
    broadcaster_id_to_remove = None
    
    # First, try to find by stream_id
    for broadcaster_id, broadcaster_data in list(broadcasters.items()):
        if broadcaster_data.get("stream_id") == stream_id:
            broadcaster_id_to_remove = broadcaster_id
            break
    
    # If not found by stream_id, try to find by user_id
    if not broadcaster_id_to_remove:
        broadcaster_id_to_remove = stream.user_id
    
    # Clean up broadcaster and viewers
    if broadcaster_id_to_remove and broadcaster_id_to_remove in broadcasters:
        try:
            broadcaster_data = broadcasters[broadcaster_id_to_remove]
            pc = broadcaster_data["pc"]
            await pc.close()
            
            # Close all viewer connections for this broadcaster
            for viewer_id in list(broadcaster_data["viewers"]):
                if viewer_id in peer_connections:
                    await peer_connections[viewer_id].close()
                    del peer_connections[viewer_id]
            
            # Remove broadcaster
            del broadcasters[broadcaster_id_to_remove]
            broadcaster_found = True
            
            # Clean up client mapping
            client_to_remove = None
            for client_id_map, broadcaster_id_map in list(client_broadcaster_mapping.items()):
                if broadcaster_id_map == broadcaster_id_to_remove:
                    client_to_remove = client_id_map
                    break
            if client_to_remove:
                del client_broadcaster_mapping[client_to_remove]
                
        except Exception as e:
            print(f"Error closing connections: {e}")
    
    # Also try to close by client_id if provided
    if client_id and client_id in client_broadcaster_mapping:
        try:
            broadcaster_id = client_broadcaster_mapping[client_id]
            if broadcaster_id in broadcasters:
                pc = broadcasters[broadcaster_id]["pc"]
                await pc.close()
                
                # Close all viewer connections
                for viewer_id in list(broadcasters[broadcaster_id]["viewers"]):
                    if viewer_id in peer_connections:
                        await peer_connections[viewer_id].close()
                        del peer_connections[viewer_id]
                
                del broadcasters[broadcaster_id]
                del client_broadcaster_mapping[client_id]
                broadcaster_found = True
        except Exception as e:
            print(f"Error closing client connection: {e}")
    
    return {
        "status": "success", 
        "message": f"Stream {stream_id} ended successfully",
        "broadcaster_found": broadcaster_found
    }


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
@router.get("/debug/status", tags=["webrtc"])
async def get_debug_status():
    """Get current WebRTC debug status"""
    try:
        from utils.webrtc import broadcasters, peer_connections, client_broadcaster_mapping
        
        return {
            "status": "ok",
            "broadcasters": {
                broadcaster_id: {
                    "stream_id": data.get("stream_id"),
                    "viewers_count": len(data.get("viewers", [])),
                    "tracks": list(data.get("tracks", {}).keys()),
                    "connection_state": data["pc"].connectionState if data.get("pc") else "unknown"
                }
                for broadcaster_id, data in broadcasters.items()
            },
            "viewers": list(peer_connections.keys()),
            "client_mappings": client_broadcaster_mapping,
            "total_broadcasters": len(broadcasters),
            "total_viewers": len(peer_connections)
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
@router.post("/test-offer", tags=["webrtc"])
async def test_webrtc_offer():
    """Simple test endpoint to verify WebRTC offer handling"""
    try:
        from utils.webrtc import broadcasters, peer_connections
        from aiortc import RTCPeerConnection, RTCSessionDescription
        
        # Create a simple test peer connection
        pc = RTCPeerConnection()
        
        # Create a simple test offer
        offer = await pc.createOffer()
        await pc.setLocalDescription(offer)
        
        # Create a test answer
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)
        
        # Clean up
        await pc.close()
        
        return {
            "status": "success",
            "message": "WebRTC offer/answer test successful",
            "offer_type": offer.type,
            "answer_type": answer.type,
            "offer_sdp_length": len(offer.sdp),
            "answer_sdp_length": len(answer.sdp)
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"WebRTC test failed: {str(e)}",
            "error_type": type(e).__name__
        }