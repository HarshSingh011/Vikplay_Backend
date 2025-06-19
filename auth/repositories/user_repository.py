"""
User repository for data access operations
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from datetime import datetime
from auth.models import User
from auth.repositories.base import SQLAlchemyRepository


class UserRepository(SQLAlchemyRepository[User]):
    """User repository with specific user operations"""
    
    def __init__(self):
        super().__init__(User)
    
    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        """Get user by email"""
        return self.get_by_field(db, "email", email)
    
    def get_by_username(self, db: Session, username: str) -> Optional[User]:
        """Get user by username"""
        return self.get_by_field(db, "username", username)
    
    def create_user(self, db: Session, email: str, username: str, hashed_password: str) -> User:
        """Create a new user"""
        user_data = {
            "email": email,
            "username": username,
            "hashed_password": hashed_password,
            "is_active": False,  # User needs to verify email first
            "is_verified": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        return self.create(db, user_data)
    
    def activate_user(self, db: Session, user: User) -> User:
        """Activate user after email verification"""
        update_data = {
            "is_active": True,
            "is_verified": True,
            "updated_at": datetime.utcnow()
        }
        return self.update(db, db_obj=user, obj_in=update_data)
    
    def update_password(self, db: Session, user: User, new_hashed_password: str) -> User:
        """Update user password"""
        update_data = {
            "hashed_password": new_hashed_password,
            "updated_at": datetime.utcnow()
        }
        return self.update(db, db_obj=user, obj_in=update_data)
    
    def update_last_login(self, db: Session, user: User) -> User:
        """Update user's last login timestamp"""
        update_data = {
            "last_login": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        return self.update(db, db_obj=user, obj_in=update_data)
    
    def get_active_users(self, db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all active users"""
        return db.query(User).filter(User.is_active == True).offset(skip).limit(limit).all()
    
    def search_users(self, db: Session, search_term: str, skip: int = 0, limit: int = 100) -> List[User]:
        """Search users by username or email"""
        return db.query(User).filter(
            (User.username.contains(search_term)) | 
            (User.email.contains(search_term))
        ).offset(skip).limit(limit).all()


# Global instance
user_repository = UserRepository()
