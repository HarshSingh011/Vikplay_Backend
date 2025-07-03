#!/usr/bin/env python3
"""
Test script to populate the database with sample data for testing the video module
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db, engine
from video.models.video_models import Base, Category, Video
from datetime import datetime

def create_sample_data():
    """Create sample categories and videos for testing"""
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Get database session
    db = next(get_db())
    
    try:
        # Create sample categories
        categories = [
            Category(name="Technology", description="Technology and programming videos"),
            Category(name="Entertainment", description="Fun and entertainment content"),
            Category(name="Education", description="Educational and learning content"),
            Category(name="Music", description="Music and audio content"),
        ]
        
        for category in categories:
            # Check if category already exists
            existing = db.query(Category).filter(Category.name == category.name).first()
            if not existing:
                db.add(category)
        
        db.commit()
        
        # Create sample videos
        tech_category = db.query(Category).filter(Category.name == "Technology").first()
        entertainment_category = db.query(Category).filter(Category.name == "Entertainment").first()
        
        if tech_category and entertainment_category:
            videos = [
                Video(
                    title="Introduction to Python",
                    description="Learn Python programming basics",
                    filename="python_intro.mp4",
                    file_path="/videos/python_intro.mp4",
                    video_url="https://example.com/python_intro.mp4",
                    thumbnail_url="https://example.com/python_intro_thumb.jpg",
                    duration=1800,  # 30 minutes
                    category_id=tech_category.id,
                    is_public=True
                ),
                Video(
                    title="Web Development with FastAPI",
                    description="Building APIs with FastAPI framework",
                    filename="fastapi_tutorial.mp4",
                    file_path="/videos/fastapi_tutorial.mp4",
                    video_url="https://example.com/fastapi_tutorial.mp4",
                    thumbnail_url="https://example.com/fastapi_tutorial_thumb.jpg",
                    duration=2700,  # 45 minutes
                    category_id=tech_category.id,
                    is_public=True
                ),
                Video(
                    title="Funny Cat Compilation",
                    description="Hilarious cat videos compilation",
                    filename="funny_cats.mp4",
                    file_path="/videos/funny_cats.mp4",
                    video_url="https://example.com/funny_cats.mp4",
                    thumbnail_url="https://example.com/funny_cats_thumb.jpg",
                    duration=600,  # 10 minutes
                    category_id=entertainment_category.id,
                    is_public=True
                ),
            ]
            
            for video in videos:
                # Check if video already exists
                existing = db.query(Video).filter(Video.title == video.title).first()
                if not existing:
                    db.add(video)
            
            db.commit()
        
        print("✅ Sample data created successfully!")
        print(f"Categories: {db.query(Category).count()}")
        print(f"Videos: {db.query(Video).count()}")
        
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_sample_data()
