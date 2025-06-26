"""
Video Services - Business logic layer for video operations
"""
import os
from typing import List, Optional
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from uuid import uuid4

from video.repositories import VideoRepository, CategoryRepository
from video.schemas import VideoCreate, Video, CategoryCreate, Category
from r2_utils import upload_file_to_r2, cleanup_incomplete_uploads

class VideoService:
    """Service layer for video business logic"""
    
    def __init__(self, db: Session):
        self.db = db
        self.video_repo = VideoRepository(db)
        self.category_repo = CategoryRepository(db)
    
    async def upload_video(
        self, 
        title: str, 
        description: str, 
        category: str, 
        file: UploadFile
    ) -> Video:
        """Upload a new video with file validation and R2 storage"""
        
        # Validate file type
        if not file.content_type.startswith("video/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be a video"
            )
        
        # Get or create category
        db_category = self.category_repo.get_or_create_category(category)
        
        try:
            # Generate unique filename
            file_ext = os.path.splitext(file.filename)[1]
            unique_filename = f"videos/{uuid4()}{file_ext}"
            
            # Upload to R2
            file_url = await upload_file_to_r2(file, unique_filename, file.content_type)
            
            # Create video record
            video_data = {
                "title": title,
                "description": description,
                "file_url": file_url,
                "category_id": db_category.id
            }
            
            return self.video_repo.create_video(video_data)
            
        except Exception as e:
            # Clean up any partial uploads
            try:
                await cleanup_incomplete_uploads(unique_filename)
            except:
                pass
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Video upload failed"
            )
    
    def get_videos(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        category_id: Optional[int] = None
    ) -> List[Video]:
        """Get videos with optional filtering"""
        return self.video_repo.get_videos(skip, limit, category_id)
    
    def get_video_by_id(self, video_id: int) -> Video:
        """Get a specific video by ID"""
        video = self.video_repo.get_video_by_id(video_id)
        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video not found"
            )
        return video
    
    def delete_video(self, video_id: int) -> dict:
        """Delete a video by ID"""
        if self.video_repo.delete_video(video_id):
            return {"message": "Video deleted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video not found"
            )
    
    def get_categories(self) -> List[Category]:
        """Get all categories"""
        return self.category_repo.get_all_categories()

class CategoryService:
    """Service layer for category business logic"""
    
    def __init__(self, db: Session):
        self.db = db
        self.category_repo = CategoryRepository(db)
    
    def create_categories_batch(self, categories: List[dict]) -> List[Category]:
        """Create multiple categories at once"""
        created_categories = []
        
        for cat_data in categories:
            # Check if category already exists
            existing = self.category_repo.get_category_by_name(cat_data["name"])
            if not existing:
                category = self.category_repo.create_category(
                    cat_data["name"], 
                    cat_data.get("description")
                )
                created_categories.append(category)
        
        return created_categories
