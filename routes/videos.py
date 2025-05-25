import os
from typing import List
from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException, status, Request
from sqlalchemy.orm import Session
from database import get_db
import models
import schemas
from uuid import uuid4
from r2_utils import upload_file_to_r2

router = APIRouter(
    prefix="/videos",
    tags=["videos"]
)

@router.post("/", response_model=schemas.Video)
async def upload_video(
    request: Request,
    title: str = Form(...),
    description: str = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Validate file type
    if not file.content_type.startswith("video/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a video"
        )
    
    # Create unique filename
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"videos/{uuid4()}{file_extension}"
    
    try:
        # Upload to Cloudflare R2
        file_url = await upload_file_to_r2(
            file=file, 
            filename=unique_filename,
            content_type=file.content_type
        )
        
        # Create DB entry
        db_video = models.Video(
            title=title,
            description=description,
            file_path=unique_filename,  # R2 key
            file_url=file_url  # Full R2 URL
        )
        
        db.add(db_video)
        db.commit()
        db.refresh(db_video)
        
        return db_video
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading video: {str(e)}"
        )

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