# Video Module - Clean Architecture Implementation

## Overview

The video module has been refactored to follow clean architecture principles with proper separation of concerns, dependency injection, and comprehensive automatic data collection for AI recommendations.

## Architecture

### Layer Structure
```
video/
├── models/           # Domain entities (SQLAlchemy models)
├── schemas/          # Data transfer objects (Pydantic schemas)
├── repositories/     # Data access layer
├── services/         # Business logic layer
└── routes/           # API endpoints layer
```

### Key Components

#### Models (`video/models/video_models.py`)
- `Video`: Core video entity with metadata
- `VideoCategory`: Video categorization
- `UserVideoHistory`: User viewing history tracking
- `UserSearchHistory`: Search behavior tracking
- `UserSession`: Session management for analytics
- `UserPreference`: User preference storage
- `VideoInteractionLog`: Detailed interaction logging

#### Repository Layer (`video/repositories/video_repository.py`)
- `VideoRepository`: CRUD operations for videos
- `CategoryRepository`: Category management
- `UserVideoHistoryRepository`: Viewing history operations
- `UserSearchHistoryRepository`: Search history operations
- `UserSessionRepository`: Session management
- `VideoInteractionRepository`: Interaction tracking

#### Service Layer (`video/services/video_service.py`)
- `VideoService`: Core video business logic
- `AnalyticsService`: Analytics and tracking logic
- `SearchService`: Search functionality
- `SessionService`: Session management logic

#### Routes (`video/routes/video_routes_clean.py`)
- Clean FastAPI routes with dependency injection
- Access token authentication via request body
- Comprehensive CRUD and analytics endpoints

## Authentication

All endpoints require authentication via access token in the request body:

```json
{
  "access_token": "your_jwt_token_here",
  // ... other request data
}
```

## API Endpoints

### Video Management

#### Create Video
```http
POST /videos/
Content-Type: application/json

{
  "access_token": "jwt_token",
  "title": "Video Title",
  "description": "Video description",
  "video_url": "https://example.com/video.mp4",
  "thumbnail_url": "https://example.com/thumb.jpg",
  "duration": 120,
  "category_id": 1
}
```

#### Get Videos
```http
GET /videos/?skip=0&limit=10
```

#### Get Video by ID
```http
GET /videos/{video_id}
```

#### Update Video
```http
PUT /videos/{video_id}
Content-Type: application/json

{
  "access_token": "jwt_token",
  "title": "Updated Title",
  "description": "Updated description"
}
```

#### Delete Video
```http
DELETE /videos/{video_id}
Content-Type: application/json

{
  "access_token": "jwt_token"
}
```

### Category Management

#### Create Category
```http
POST /categories/
Content-Type: application/json

{
  "access_token": "jwt_token",
  "name": "Category Name",
  "description": "Category description"
}
```

#### Get Categories
```http
GET /categories/
```

### Automatic Data Collection for AI

#### Track Video Viewing
```http
POST /videos/track/watch
Content-Type: application/json

{
  "access_token": "jwt_token",
  "video_id": 1,
  "progress": 75.5,
  "total_duration": 120,
  "quality": "1080p",
  "device_info": "Chrome/Windows",
  "network_quality": "high"
}
```

#### Track Video Engagement
```http
POST /videos/track/engagement
Content-Type: application/json

{
  "access_token": "jwt_token",
  "video_id": 1,
  "event_type": "like",
  "engagement_value": 1,
  "device_info": "Chrome/Windows"
}
```

#### Track Search Behavior
```http
POST /videos/track/search
Content-Type: application/json

{
  "access_token": "jwt_token",
  "query": "funny cats",
  "category": "entertainment",
  "results_count": 25,
  "device_info": "Chrome/Windows"
}
```

#### Track Session Data
```http
POST /videos/track/session
Content-Type: application/json

{
  "access_token": "jwt_token",
  "session_duration": 1800,
  "videos_watched": 5,
  "interactions_count": 12,
  "device_info": "Chrome/Windows",
  "ip_address": "192.168.1.1"
}
```

### Analytics Endpoints

#### Get User Analytics
```http
POST /videos/analytics/user
Content-Type: application/json

{
  "access_token": "jwt_token",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31"
}
```

#### Get Video Analytics
```http
GET /videos/analytics/video/{video_id}
```

#### Get Popular Videos
```http
GET /videos/analytics/popular?period=week&limit=10
```

#### Get User Recommendations
```http
POST /videos/recommendations
Content-Type: application/json

{
  "access_token": "jwt_token",
  "limit": 10
}
```

## Data Collection Features

### Automatic Tracking
The system automatically collects:

1. **Viewing History**: Complete watch history with progress tracking
2. **Engagement Data**: Likes, comments, shares, ratings
3. **Search Behavior**: Search queries, filters, result interactions
4. **Session Patterns**: Session duration, navigation patterns, time-based behavior
5. **Device Information**: Browser, OS, screen resolution, network quality
6. **Interaction Logs**: Detailed interaction tracking for ML/AI

### AI-Ready Data Structure
All collected data is structured for machine learning applications:
- Consistent timestamps and user identification
- Normalized engagement metrics
- Categorical data for pattern recognition
- Session-based aggregation
- Device and context information

## Error Handling

All endpoints return consistent error responses:

```json
{
  "detail": "Error description",
  "status_code": 400
}
```

Common status codes:
- `200`: Success
- `201`: Created
- `400`: Bad Request
- `401`: Unauthorized (invalid/expired token)
- `404`: Not Found
- `422`: Validation Error
- `500`: Internal Server Error

## Dependencies

The module uses dependency injection for clean separation:
- Database sessions via `get_db()`
- Services via dependency functions
- Authentication via token verification

## Migration from Legacy

The old routes (`video_routes.py`) have been replaced with the clean architecture implementation (`video_routes_clean.py`). The new system:

1. Uses access tokens in request body instead of headers
2. Implements proper layered architecture
3. Provides comprehensive data collection
4. Includes better error handling and validation
5. Supports advanced analytics and recommendations

## Testing

To test the API endpoints, ensure:
1. The server is running (`uvicorn main:app --reload`)
2. You have a valid JWT access token
3. The database is properly initialized
4. All required dependencies are installed

Example test with curl:
```bash
curl -X POST "http://localhost:8000/videos/track/watch" \
  -H "Content-Type: application/json" \
  -d '{
    "access_token": "your_jwt_token",
    "video_id": 1,
    "progress": 50.0,
    "total_duration": 120
  }'
```
