import sys
import os
# Add parent directory to path so we can import from root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal, engine
import video.models as models
from video.services import CategoryService

# Create tables if they don't exist
models.Base.metadata.create_all(bind=engine)

# Initial categories
initial_categories = [
    {"name": "Entertainment", "description": "Fun and entertaining videos"},
    {"name": "Education", "description": "Educational content"},
    {"name": "Sports", "description": "Sports highlights and events"},
    {"name": "Music", "description": "Music videos and performances"},
    {"name": "Gaming", "description": "Video game content"},
    {"name": "News", "description": "Current events and news coverage"},
    {"name": "Technology", "description": "Tech reviews and tutorials"},
    {"name": "Travel", "description": "Travel vlogs and destination guides"},
    {"name": "Cooking", "description": "Food recipes and cooking tutorials"},
    {"name": "Fitness", "description": "Workout videos and fitness tips"}
]

def create_initial_categories():
    """Create initial video categories"""
    db = SessionLocal()
    try:
        # Check if categories already exist
        existing_count = db.query(models.Category).count()
        if existing_count == 0:
            category_service = CategoryService(db)
            created = category_service.create_categories_batch(initial_categories)
            
            print(f"Created {len(created)} categories:")
            for category in created:
                print(f"  - {category.name}: {category.description}")
        else:
            print(f"Categories already exist. Found {existing_count} categories.")
            
    except Exception as e:
        print(f"Error creating categories: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_initial_categories()