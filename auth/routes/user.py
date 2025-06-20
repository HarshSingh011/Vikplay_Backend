"""
User-related routes - profile, user management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from database import get_db
from auth.schemas import UserResponse
from auth.services import get_user_service
import logging

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Security scheme
security = HTTPBearer()

@router.get("/me", response_model=UserResponse)
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Get current authenticated user information
    """
    try:
        user_service = get_user_service(db)
        
        # Get user by token
        result = user_service.get_user_by_token(credentials.credentials)
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=result.message,
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return UserResponse.from_orm(result.data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get current user error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user information"
        )

@router.get("/health")
async def health_check():
    """
    Health check endpoint for auth service
    """
    return {"status": "healthy", "service": "authentication"}
