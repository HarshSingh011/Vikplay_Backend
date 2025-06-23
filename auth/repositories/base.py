"""
Base repository interface and implementation
"""
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import declarative_base

T = TypeVar('T')

class BaseRepository(ABC, Generic[T]):
    """Abstract base repository interface"""
    
    @abstractmethod
    def create(self, db: Session, obj_in: dict) -> T:
        """Create a new record"""
        pass
    
    @abstractmethod
    def get(self, db: Session, id: Any) -> Optional[T]:
        """Get a record by ID"""
        pass
    
    @abstractmethod
    def get_by_field(self, db: Session, field: str, value: Any) -> Optional[T]:
        """Get a record by a specific field"""
        pass
    
    @abstractmethod
    def get_multi(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[T]:
        """Get multiple records"""
        pass
    
    @abstractmethod
    def update(self, db: Session, *, db_obj: T, obj_in: dict) -> T:
        """Update a record"""
        pass
    
    @abstractmethod
    def delete(self, db: Session, *, id: Any) -> T:
        """Delete a record"""
        pass


class SQLAlchemyRepository(BaseRepository[T]):
    """Base SQLAlchemy repository implementation"""
    
    def __init__(self, model: type[T]):
        self.model = model
    
    def create(self, db: Session, obj_in: dict) -> T:
        """Create a new record"""
        db_obj = self.model(**obj_in)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def get(self, db: Session, id: Any) -> Optional[T]:
        """Get a record by ID"""
        return db.query(self.model).filter(self.model.id == id).first()
    
    def get_by_field(self, db: Session, field: str, value: Any) -> Optional[T]:
        """Get a record by a specific field"""
        return db.query(self.model).filter(getattr(self.model, field) == value).first()
    
    def get_multi(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[T]:
        """Get multiple records"""
        return db.query(self.model).offset(skip).limit(limit).all()
    
    def update(self, db: Session, *, db_obj: T, obj_in: dict) -> T:
        """Update a record"""
        for field, value in obj_in.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def delete(self, db: Session, *, id: Any) -> T:
        """Delete a record"""
        obj = db.query(self.model).get(id)
        db.delete(obj)
        db.commit()
        return obj
