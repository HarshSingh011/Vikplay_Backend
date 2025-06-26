from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class Category(CategoryBase):
    id: int

    class Config:
        from_attributes = True

class VideoBase(BaseModel):
    title: str
    description: Optional[str] = None
    category_id: Optional[int] = None

class VideoCreate(VideoBase):
    pass

class Video(VideoBase):
    id: int
    file_url: str
    created_at: datetime
    category: Optional[Category] = None

    class Config:
        from_attributes = True
