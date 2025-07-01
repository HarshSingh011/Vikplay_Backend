"""
Video routes with automatic data collection for AI recommendations
"""
import uuid
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_

from database import get_db
from auth.utils.jwt_token import get_current_user
from video.models.video_models import (
    Video, Category, UserVideoHistory, UserSearchHistory, 
    UserSession, UserPreferences, VideoInteractionLog
)
from video.schemas.video_schemas import (
    VideoCreate, VideoUpdate, VideoResponse, CategoryCreate, CategoryResponse,
    WatchProgressUpdateEnhanced, VideoEngagement, VideoInteraction,
    SearchQueryLog, SearchResultClick, SessionStart, SessionActivity, SessionEnd,
    UserVideoHistoryResponse, UserSearchHistoryResponse, UserSessionResponse,
    UserPreferencesUpdate, UserAnalytics, VideoAnalytics
)

router = APIRouter(prefix="/api/videos", tags=["videos"])


# ====== AUTOMATIC DATA COLLECTION ENDPOINTS ======

@router.post("/track/watch-progress")
async def track_watch_progress(
    progress: WatchProgressUpdateEnhanced,
    request: Request,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    AUTOMATIC COLLECTION: Viewing History
    Called automatically by video player to track viewing progress
    """
    # Get device info automatically
    device_info = extract_device_info(request)
    
    # Record or update viewing history
    history_entry = db.query(UserVideoHistory).filter(
        and_(
            UserVideoHistory.user_id == current_user.id,
            UserVideoHistory.video_id == progress.video_id,
            UserVideoHistory.session_id == progress.session_id
        )
    ).first()
    
    if history_entry:
        # Update existing entry
        history_entry.watch_duration = progress.watch_duration
        history_entry.completion_percentage = progress.completion_percentage
    else:
        # Create new entry
        history_entry = UserVideoHistory(
            user_id=current_user.id,
            video_id=progress.video_id,
            watch_duration=progress.watch_duration,
            completion_percentage=progress.completion_percentage,
            device_type=device_info["device_type"],
            session_id=progress.session_id or str(uuid.uuid4())
        )
        db.add(history_entry)
    
    # Update video engagement metrics in background
    background_tasks.add_task(update_video_metrics, progress.video_id, db)
    
    db.commit()
    return {"status": "success", "message": "Watch progress tracked"}


@router.post("/track/engagement")
async def track_engagement(
    engagement: VideoEngagement,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    AUTOMATIC COLLECTION: Engagement Metrics
    Called when user likes, rates, shares, or bookmarks a video
    """
    # Find or create history entry
    history_entry = db.query(UserVideoHistory).filter(
        and_(
            UserVideoHistory.user_id == current_user.id,
            UserVideoHistory.video_id == engagement.video_id
        )
    ).order_by(desc(UserVideoHistory.watched_at)).first()
    
    if history_entry:
        # Update engagement data
        if engagement.rating is not None:
            history_entry.rating = engagement.rating
        if engagement.liked is not None:
            history_entry.liked = engagement.liked
        history_entry.shared = engagement.shared
        history_entry.bookmarked = engagement.bookmarked
        
        db.commit()
        
        # Update video aggregate metrics
        update_video_engagement_metrics(engagement.video_id, db)
        
        return {"status": "success", "message": "Engagement tracked"}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video viewing history not found"
        )


@router.post("/track/interaction")
async def track_interaction(
    interaction: VideoInteraction,
    request: Request,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    AUTOMATIC COLLECTION: Detailed Engagement
    Tracks every user interaction with videos
    """
    device_info = extract_device_info(request)
    
    interaction_log = VideoInteractionLog(
        user_id=current_user.id,
        video_id=interaction.video_id,
        session_id=interaction.session_id,
        interaction_type=interaction.interaction_type,
        interaction_value=interaction.interaction_value,
        video_timestamp=interaction.video_timestamp,
        device_type=device_info["device_type"]
    )
    
    db.add(interaction_log)
    db.commit()
    
    return {"status": "success", "message": "Interaction tracked"}


@router.post("/search")
async def search_videos(
    search_log: SearchQueryLog,
    request: Request,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    AUTOMATIC COLLECTION: Search Queries
    Enhanced search that automatically logs search behavior
    """
    device_info = extract_device_info(request)
    
    # Perform the search
    search_results = db.query(Video).filter(
        Video.title.contains(search_log.search_query)
    ).limit(20).all()
    
    # Log the search automatically
    search_history = UserSearchHistory(
        user_id=current_user.id,
        search_query=search_log.search_query,
        results_count=len(search_results),
        search_filters=search_log.search_filters,
        device_type=device_info["device_type"]
    )
    
    db.add(search_history)
    db.commit()
    
    # Return search results with search_id for click tracking
    return {
        "search_id": search_history.id,
        "results": [VideoResponse.from_orm(video) for video in search_results],
        "total_results": len(search_results)
    }


@router.post("/search/click")
async def track_search_click(
    click: SearchResultClick,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    AUTOMATIC COLLECTION: Search Result Clicks
    Called when user clicks on a search result
    """
    # Update the search history with click information
    search_history = db.query(UserSearchHistory).filter(
        and_(
            UserSearchHistory.id == click.search_id,
            UserSearchHistory.user_id == current_user.id
        )
    ).first()
    
    if search_history:
        search_history.clicked_video_id = click.clicked_video_id
        search_history.click_position = click.click_position
        search_history.time_to_click = click.time_to_click
        db.commit()
        
        return {"status": "success", "message": "Search click tracked"}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Search history not found"
        )


@router.post("/session/start")
async def start_session(
    session_data: SessionStart,
    request: Request,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    AUTOMATIC COLLECTION: Session Patterns
    Called when user starts a new session
    """
    device_info = extract_device_info(request)
    
    # Calculate time patterns
    now = datetime.utcnow()
    time_patterns = calculate_time_patterns(now)
    
    session = UserSession(
        user_id=current_user.id,
        session_id=session_data.session_id,
        device_type=device_info["device_type"],
        browser=device_info["browser"],
        os=device_info["os"],
        ip_address=device_info["ip_address"],
        user_agent=request.headers.get("user-agent"),
        time_of_day=time_patterns["time_of_day"],
        day_of_week=time_patterns["day_of_week"],
        is_weekend=time_patterns["is_weekend"]
    )
    
    db.add(session)
    db.commit()
    
    return {"status": "success", "session_id": session_data.session_id}


@router.put("/session/activity")
async def update_session_activity(
    activity: SessionActivity,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    AUTOMATIC COLLECTION: Session Activity
    Called periodically to update session activity
    """
    session = db.query(UserSession).filter(
        and_(
            UserSession.session_id == activity.session_id,
            UserSession.user_id == current_user.id
        )
    ).first()
    
    if session:
        session.videos_watched = activity.videos_watched
        session.searches_performed = activity.searches_performed
        session.videos_liked = activity.videos_liked
        session.videos_shared = activity.videos_shared
        db.commit()
        
        return {"status": "success", "message": "Session activity updated"}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )


@router.post("/session/end")
async def end_session(
    session_end: SessionEnd,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    AUTOMATIC COLLECTION: Session End
    Called when user session ends
    """
    session = db.query(UserSession).filter(
        and_(
            UserSession.session_id == session_end.session_id,
            UserSession.user_id == current_user.id
        )
    ).first()
    
    if session:
        session.session_end = datetime.utcnow()
        session.session_duration = session_end.session_duration
        db.commit()
        
        return {"status": "success", "message": "Session ended"}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )


# ====== ANALYTICS ENDPOINTS FOR AI ======

@router.get("/analytics/user", response_model=UserAnalytics)
async def get_user_analytics(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive user analytics for AI recommendations
    """
    # Get user's viewing history
    history = db.query(UserVideoHistory).filter(
        UserVideoHistory.user_id == current_user.id
    ).all()
    
    if not history:
        return UserAnalytics(
            total_videos_watched=0,
            total_watch_time=0,
            average_completion_rate=0.0,
            favorite_categories=[],
            most_active_times=[],
            preferred_video_length=0,
            engagement_score=0.0,
            recent_interests=[]
        )
    
    # Calculate analytics
    total_videos = len(history)
    total_watch_time = sum(h.watch_duration for h in history)
    avg_completion = sum(h.completion_percentage for h in history) / total_videos
    
    # Get favorite categories
    category_counts = db.query(
        Category.name, func.count(UserVideoHistory.id).label('count')
    ).join(Video).join(UserVideoHistory).filter(
        UserVideoHistory.user_id == current_user.id
    ).group_by(Category.name).order_by(desc('count')).limit(5).all()
    
    favorite_categories = [
        {"category": cat.name, "count": cat.count} 
        for cat in category_counts
    ]
    
    # Get session patterns for active times
    sessions = db.query(UserSession).filter(
        UserSession.user_id == current_user.id
    ).all()
    
    time_counts = {}
    for session in sessions:
        if session.time_of_day:
            time_counts[session.time_of_day] = time_counts.get(session.time_of_day, 0) + 1
    
    most_active_times = sorted(time_counts.keys(), key=lambda x: time_counts[x], reverse=True)[:3]
    
    # Calculate engagement score
    liked_videos = len([h for h in history if h.liked is True])
    engagement_score = (liked_videos / total_videos) * 100 if total_videos > 0 else 0
    
    # Get recent interests (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_categories = db.query(Category.name).join(Video).join(UserVideoHistory).filter(
        and_(
            UserVideoHistory.user_id == current_user.id,
            UserVideoHistory.watched_at >= thirty_days_ago
        )
    ).distinct().all()
    
    recent_interests = [cat.name for cat in recent_categories]
    
    return UserAnalytics(
        total_videos_watched=total_videos,
        total_watch_time=total_watch_time,
        average_completion_rate=avg_completion,
        favorite_categories=favorite_categories,
        most_active_times=most_active_times,
        preferred_video_length=int(total_watch_time / total_videos) if total_videos > 0 else 0,
        engagement_score=engagement_score,
        recent_interests=recent_interests
    )


# ====== UTILITY FUNCTIONS ======

def extract_device_info(request: Request) -> dict:
    """Extract device information from request"""
    user_agent = request.headers.get("user-agent", "")
    
    # Simple device detection (you can use a library like user-agents for better detection)
    device_type = "desktop"
    if "mobile" in user_agent.lower():
        device_type = "mobile"
    elif "tablet" in user_agent.lower():
        device_type = "tablet"
    
    return {
        "device_type": device_type,
        "browser": extract_browser(user_agent),
        "os": extract_os(user_agent),
        "ip_address": request.client.host if request.client else None
    }


def extract_browser(user_agent: str) -> str:
    """Extract browser from user agent"""
    user_agent = user_agent.lower()
    if "chrome" in user_agent:
        return "chrome"
    elif "firefox" in user_agent:
        return "firefox"
    elif "safari" in user_agent:
        return "safari"
    elif "edge" in user_agent:
        return "edge"
    else:
        return "unknown"


def extract_os(user_agent: str) -> str:
    """Extract OS from user agent"""
    user_agent = user_agent.lower()
    if "windows" in user_agent:
        return "windows"
    elif "mac" in user_agent:
        return "macos"
    elif "linux" in user_agent:
        return "linux"
    elif "android" in user_agent:
        return "android"
    elif "ios" in user_agent:
        return "ios"
    else:
        return "unknown"


def calculate_time_patterns(dt: datetime) -> dict:
    """Calculate time-based patterns"""
    hour = dt.hour
    
    if 6 <= hour < 12:
        time_of_day = "morning"
    elif 12 <= hour < 17:
        time_of_day = "afternoon"
    elif 17 <= hour < 22:
        time_of_day = "evening"
    else:
        time_of_day = "night"
    
    days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    day_of_week = days[dt.weekday()]
    is_weekend = dt.weekday() >= 5
    
    return {
        "time_of_day": time_of_day,
        "day_of_week": day_of_week,
        "is_weekend": is_weekend
    }


def update_video_metrics(video_id: int, db: Session):
    """Background task to update video metrics"""
    # Calculate and update video engagement metrics
    history_entries = db.query(UserVideoHistory).filter(
        UserVideoHistory.video_id == video_id
    ).all()
    
    if history_entries:
        video = db.query(Video).filter(Video.id == video_id).first()
        if video:
            # Update metrics
            video.view_count = len(history_entries)
            video.average_watch_time = sum(h.watch_duration for h in history_entries) / len(history_entries)
            video.completion_rate = sum(h.completion_percentage for h in history_entries) / len(history_entries)
            
            # Count likes/dislikes
            likes = len([h for h in history_entries if h.liked is True])
            dislikes = len([h for h in history_entries if h.liked is False])
            
            video.like_count = likes
            video.dislike_count = dislikes
            
            db.commit()


def update_video_engagement_metrics(video_id: int, db: Session):
    """Update video engagement metrics immediately"""
    update_video_metrics(video_id, db)
