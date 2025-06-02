import os
import secrets
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status, Request, Form, File, UploadFile
from sqlalchemy.orm import Session
from database import get_db
import models
import schemas.streaming as schemas
from utils.websocket import ConnectionManager
from r2_utils import upload_file_to_r2
from utils.webrtc import get_viewer_count, get_active_broadcasters
from schemas.schemas import StreamCreate, Stream, StreamPublic, ChatMessage

router = APIRouter(
    prefix="/streaming",
    tags=["streaming"]
)

# Initialize the connection manager for chat
manager = ConnectionManager()

# Create a new stream
@router.post("/streams", response_model=schemas.Stream)
async def create_stream(
    stream: schemas.StreamCreate,
    db: Session = Depends(get_db)
):
    # Generate a unique stream key
    stream_key = secrets.token_urlsafe(16)
    
    # Create stream record
    db_stream = models.Stream(
        title=stream.title,
        description=stream.description,
        user_id=stream.user_id,
        stream_key=stream_key,
        is_live=False,
        viewer_count=0
    )
    
    db.add(db_stream)
    db.commit()
    db.refresh(db_stream)
    
    return db_stream

# Get all active streams
@router.get("/streams", response_model=List[schemas.StreamPublic])
async def get_streams(
    skip: int = 0, 
    limit: int = 100,
    live_only: bool = False,
    db: Session = Depends(get_db)
):
    query = db.query(models.Stream)
    
    if live_only:
        query = query.filter(models.Stream.is_live == True)
    
    streams = query.order_by(models.Stream.created_at.desc()).offset(skip).limit(limit).all()
    
    # Update viewer counts from WebRTC
    active_broadcasters = get_active_broadcasters()
    for stream in streams:
        if stream.user_id in active_broadcasters:
            stream.viewer_count = get_viewer_count(stream.user_id)
    
    return streams

# Get a specific stream
@router.get("/streams/{stream_id}", response_model=schemas.StreamPublic)
async def get_stream(
    stream_id: int,
    db: Session = Depends(get_db)
):
    stream = db.query(models.Stream).filter(models.Stream.id == stream_id).first()
    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")
    
    # Update viewer count from WebRTC
    if stream.user_id in get_active_broadcasters():
        stream.viewer_count = get_viewer_count(stream.user_id)
    
    return stream

# Upload stream thumbnail
@router.post("/streams/{stream_id}/thumbnail")
async def upload_thumbnail(
    stream_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    stream = db.query(models.Stream).filter(models.Stream.id == stream_id).first()
    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")
    
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )
    
    # Upload thumbnail to R2
    filename = f"thumbnails/stream_{stream_id}_{secrets.token_urlsafe(8)}.jpg"
    file_url = await upload_file_to_r2(file, filename, file.content_type)
    
    # Update stream record
    stream.thumbnail_url = file_url
    db.commit()
    
    return {"thumbnail_url": file_url}

# Get chat history for a stream
@router.get("/streams/{stream_id}/chat", response_model=List[schemas.ChatMessage])
async def get_chat_history(
    stream_id: int,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    # Check if stream exists
    stream = db.query(models.Stream).filter(models.Stream.id == stream_id).first()
    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")
    
    # Get recent chat messages
    messages = db.query(models.ChatMessage)\
        .filter(models.ChatMessage.stream_id == stream_id)\
        .order_by(models.ChatMessage.created_at.desc())\
        .limit(limit)\
        .all()
    
    # Return in chronological order
    messages.reverse()
    
    return messages

# WebSocket endpoint for chat
@router.websocket("/ws/chat/{stream_id}")
async def websocket_chat_endpoint(
    websocket: WebSocket, 
    stream_id: int,
    db: Session = Depends(get_db)
):
    # Check if stream exists
    stream = db.query(models.Stream).filter(models.Stream.id == stream_id).first()
    if not stream:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    # Connect to the WebSocket
    await manager.connect(websocket, stream_id)
    
    try:
        # Update stream's viewer count in DB periodically
        stream.viewer_count = manager.get_viewer_count(stream_id)
        db.commit()
        
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            # Extract message content
            message_text = data.get("message", "")
            user_id = data.get("user_id", "anonymous")
            username = data.get("username", "Anonymous")
            
            if not message_text:
                continue
            
            # Create chat message in DB
            db_message = models.ChatMessage(
                stream_id=stream_id,
                user_id=user_id,
                username=username,
                message=message_text
            )
            
            db.add(db_message)
            db.commit()
            db.refresh(db_message)
            
            # Broadcast message to all connected clients
            await manager.broadcast(stream_id, {
                "type": "chat_message",
                "id": db_message.id,
                "user_id": db_message.user_id,
                "username": db_message.username,
                "message": db_message.message,
                "created_at": db_message.created_at.isoformat()
            })
            
    except WebSocketDisconnect:
        # Handle client disconnect
        manager.disconnect(websocket, stream_id)
        
        # Update stream's viewer count in DB
        stream.viewer_count = manager.get_viewer_count(stream_id)
        db.commit()