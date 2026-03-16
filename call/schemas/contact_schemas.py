"""
Pydantic schemas for contact operations.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ContactCreate(BaseModel):
    """Schema for creating a contact"""
    email: str = Field(..., description="Email of the user to add as contact")
    nickname: str = Field(..., description="Nickname for this contact")


class ContactUpdate(BaseModel):
    """Schema for updating a contact"""
    nickname: str = Field(..., description="New nickname for contact")


class ContactResponse(BaseModel):
    """Schema for contact response"""
    id: str
    user_id: int
    contact_user_id: int
    nickname: str
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class ContactListResponse(BaseModel):
    """Schema for contact list response"""
    contacts: List[ContactResponse]
    total: int
    page: int
    page_size: int
