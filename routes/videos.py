import os
from typing import List, Optional
from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException, status, Request
from sqlalchemy.orm import Session
from database import get_db
import models.models as models
from uuid import uuid4
from schemas.schemas import VideoCreate, Video
import schemas.schemas as schemas
from r2_utils import upload_file_to_r2, cleanup_incomplete_uploads

router = APIRouter(
    prefix="/videos",
    tags=["videos"]
)

@router.post("/", response_model=schemas.Video)
async def upload_video(
    request: Request,
    title: str = Form(...),
    description: str = Form(None),
    category: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload a new video with required category selection (by name)
    """
    # Find category by name (case insensitive)
    db_category = db.query(models.Category).filter(
        models.Category.name.ilike(category)
    ).first()
    
    # If category doesn't exist, create it
    if not db_category:
        db_category = models.Category(
            name=category,
            description=f"Videos about {category}"
        )
        db.add(db_category)
        db.commit()
        db.refresh(db_category)
        
    # Validate file type
    if not file.content_type.startswith("video/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="File must be a video"
        )
    
    try:
        # Generate unique filename
        file_ext = os.path.splitext(file.filename)[1]
        unique_filename = f"videos/{uuid4()}{file_ext}"
        
        # Upload to R2
        file_url = await upload_file_to_r2(file, unique_filename, file.content_type)
        
        # Create database record
        db_video = models.Video(
            title=title,
            description=description,
            file_url=file_url,
            category_id=db_category.id
        )
        
        db.add(db_video)
        db.commit()
        db.refresh(db_video)
        
        return db_video
        
    except Exception as e:
        # Try to clean up any partial uploads
        try:
            await cleanup_incomplete_uploads(unique_filename)
        except:
            # Ignore cleanup errors
            pass
            
        # Return specific error message
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Uploading failed"
        )

# Get all videos with optional category filter
@router.get("/", response_model=List[schemas.Video])
def get_videos(
    skip: int = 0, 
    limit: int = 100, 
    category_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Get all videos with optional category filter
    """
    query = db.query(models.Video)
    
    if category_id is not None:
        query = query.filter(models.Video.category_id == category_id)
        
    videos = query.order_by(models.Video.created_at.desc()).offset(skip).limit(limit).all()
    return videos

