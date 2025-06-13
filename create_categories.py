from database import SessionLocal, engine
import models.models as models

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
    db = SessionLocal()
    try:
        # Check if categories already exist
        existing_count = db.query(models.Category).count()
        if existing_count == 0:
            # Add initial categories
            for category_data in initial_categories:
                category = models.Category(**category_data)
                db.add(category)
            db.commit()
            print(f"Added {len(initial_categories)} initial categories")
        else:
            print(f"Categories already exist. Found {existing_count} categories.")
    finally:
        db.close()

if __name__ == "__main__":
    create_initial_categories()