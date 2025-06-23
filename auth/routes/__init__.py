"""
Authentication routes exports
"""
from fastapi import APIRouter
from .auth import router as auth_router
from .password import router as password_router  
from .user import router as user_router

# Main auth router
router = APIRouter(prefix="/auth", tags=["authentication"])

# Include sub-routers
router.include_router(auth_router)
router.include_router(password_router)
router.include_router(user_router)
