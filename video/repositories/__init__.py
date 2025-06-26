"""
Video Repository - Data access layer for video operations
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from video.models import Video, Category

class VideoRepository:
    """Repository for video-related database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_video(self, video_data: dict) -> Video:
        """Create a new video record"""
        db_video = Video(**video_data)
        self.db.add(db_video)
        self.db.commit()
        self.db.refresh(db_video)
        return db_video
    
    def get_video_by_id(self, video_id: int) -> Optional[Video]:
        """Get video by ID"""
        return self.db.query(Video).filter(Video.id == video_id).first()
    
    def get_videos(self, skip: int = 0, limit: int = 100, category_id: Optional[int] = None) -> List[Video]:
        """Get videos with optional category filter"""
        query = self.db.query(Video)
        
        if category_id is not None:
            query = query.filter(Video.category_id == category_id)
        
        return query.order_by(desc(Video.created_at)).offset(skip).limit(limit).all()
    
    def delete_video(self, video_id: int) -> bool:
        """Delete video by ID"""
        video = self.get_video_by_id(video_id)
        if video:
            self.db.delete(video)
            self.db.commit()
            return True
        return False
    
    def update_video(self, video_id: int, update_data: dict) -> Optional[Video]:
        """Update video information"""
        video = self.get_video_by_id(video_id)
        if video:
            for key, value in update_data.items():
                setattr(video, key, value)
            self.db.commit()
            self.db.refresh(video)
            return video
        return None

class CategoryRepository:
    """Repository for category-related database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_category(self, name: str, description: str = None) -> Category:
        """Create a new category"""
        db_category = Category(name=name, description=description)
        self.db.add(db_category)
        self.db.commit()
        self.db.refresh(db_category)
        return db_category
    
    def get_category_by_name(self, name: str) -> Optional[Category]:
        """Get category by name (case insensitive)"""
        return self.db.query(Category).filter(Category.name.ilike(name)).first()
    
    def get_category_by_id(self, category_id: int) -> Optional[Category]:
        """Get category by ID"""
        return self.db.query(Category).filter(Category.id == category_id).first()
    
    def get_all_categories(self) -> List[Category]:
        """Get all categories"""
        return self.db.query(Category).all()
    
    def get_or_create_category(self, name: str, description: str = None) -> Category:
        """Get existing category or create new one"""
        category = self.get_category_by_name(name)
        if not category:
            category = self.create_category(name, description or f"Videos about {name}")
        return category
