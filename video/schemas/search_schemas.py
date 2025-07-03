"""
Search schemas for the VikPay Backend
Request/Response models for search operations and tracking
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


# 2. SEARCH QUERY TRACKING
class SearchQueryLog(BaseModel):
    """
    AUTOMATIC COLLECTION: Search Queries
    Logged automatically when user searches
    """
    search_query: str = Field(..., max_length=500)
    search_filters: Optional[Dict[str, Any]] = None
    device_type: Optional[str] = None


class SearchResultClick(BaseModel):
    """
    AUTOMATIC COLLECTION: Search Interaction
    Logged when user clicks search result
    """
    search_id: int  # ID of the search query
    clicked_video_id: int
    click_position: int  # position in search results
    time_to_click: Optional[float] = None  # seconds from search to click


class UserSearchHistoryResponse(BaseModel):
    """Response schema for user search history"""
    id: int
    search_query: str
    searched_at: datetime
    results_count: int
    clicked_video_id: Optional[int] = None
    click_position: Optional[int] = None

    class Config:
        from_attributes = True
