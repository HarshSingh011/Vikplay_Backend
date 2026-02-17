"""
Script to create test users for video calling
"""
import sys
sys.path.append('.')

from sqlalchemy.orm import Session
from database import SessionLocal, engine
from auth.models import User, Base
from auth.utils.password import PasswordUtils
from datetime import datetime

# Create tables
Base.metadata.create_all(bind=engine)

def create_test_users():
    db = SessionLocal()
    pwd_utils = PasswordUtils()
    
    try:
        # Check if users already exist
        existing_user1 = db.query(User).filter(User.email == "caller@test.com").first()
        existing_user2 = db.query(User).filter(User.email == "receiver@test.com").first()
        
        users_created = []
        
        if not existing_user1:
            user1 = User(
                id=1,
                email="caller@test.com",
                username="caller_test_user",
                phone_number="+1234567890",
                hashed_password=pwd_utils.hash_password("password123"),
                is_active=True,
                is_verified=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(user1)
            users_created.append("User 1 (Caller)")
        
        if not existing_user2:
            user2 = User(
                id=2,
                email="receiver@test.com",
                username="receiver_test_user",
                phone_number="+1234567891",
                hashed_password=pwd_utils.hash_password("password123"),
                is_active=True,
                is_verified=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(user2)
            users_created.append("User 2 (Receiver)")
        
        # Add more test users
        for i in range(3, 6):
            existing = db.query(User).filter(User.email == f"user{i}@test.com").first()
            if not existing:
                user = User(
                    id=i,
                    email=f"user{i}@test.com",
                    username=f"test_user_{i}",
                    phone_number=f"+123456789{i}",
                    hashed_password=pwd_utils.hash_password("password123"),
                    is_active=True,
                    is_verified=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(user)
                users_created.append(f"User {i}")
        
        db.commit()
        
        if users_created:
            print("✅ Created test users:")
            for user in users_created:
                print(f"   - {user}")
        else:
            print("ℹ️  All test users already exist")
        
        # List all users
        print("\n📋 All test users in database:")
        all_users = db.query(User).all()
        for user in all_users:
            print(f"   ID: {user.id}, Username: {user.username}, Email: {user.email}")
        
    except Exception as e:
        print(f"❌ Error creating test users: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_test_users()
