import os
import shutil
from typing import List
from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException, status, Request
from sqlalchemy.orm import Session
from database import get_db
import models
import schemas
from uuid import uuid4

router = APIRouter(
    prefix="/videos",
    tags=["videos"]
)

UPLOAD_DIR = "static/videos"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/", response_model=schemas.Video)
async def upload_video(
    request: Request,
    title: str = Form(...),
    description: str = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if not file.content_type.startswith("video/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a video"
        )
    
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid4()}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    base_url = str(request.base_url).rstrip('/')
    file_url = f"{base_url}/static/videos/{unique_filename}"
    
    db_video = models.Video(
        title=title,
        description=description,
        file_path=file_path,
        file_url=file_url
    )
    
    db.add(db_video)
    db.commit()
    db.refresh(db_video)
    
    return db_video

@router.get("/", response_model=List[schemas.Video])
def get_videos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    videos = db.query(models.Video).offset(skip).limit(limit).all()
    return videos

@router.get("/{video_id}", response_model=schemas.Video)
def get_video(video_id: int, db: Session = Depends(get_db)):
    video = db.query(models.Video).filter(models.Video.id == video_id).first()
    if video is None:
        raise HTTPException(status_code=404, detail="Video not found")
    return video