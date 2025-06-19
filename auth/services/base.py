"""
Base service interface and implementation
"""
from abc import ABC, abstractmethod
from sqlalchemy.orm import Session


class BaseService(ABC):
    """Abstract base service interface"""
    
    def __init__(self, db: Session):
        self.db = db


class AuthenticationError(Exception):
    """Authentication related errors"""
    pass


class ValidationError(Exception):
    """Validation related errors"""
    pass


class NotFoundError(Exception):
    """Resource not found errors"""
    pass


class RateLimitError(Exception):
    """Rate limiting errors"""
    pass


class ServiceResult:
    """Standard service result wrapper"""
    
    def __init__(self, success: bool, data=None, message: str = "", errors: list = None):
        self.success = success
        self.data = data
        self.message = message
        self.errors = errors or []
    
    @classmethod
    def success_result(cls, data=None, message: str = ""):
        """Create a success result"""
        return cls(success=True, data=data, message=message)
    
    @classmethod
    def error_result(cls, message: str, errors: list = None):
        """Create an error result"""
        return cls(success=False, message=message, errors=errors or [])
