# AI-Powered Video Recommendation System

## Overview
VikPay now includes an advanced AI-powered video recommendation system built with **Ollama** and **ChromaDB**. This system provides personalized video recommendations based on user behavior, content similarity, and collaborative filtering.

## 🚀 Technologies Used

### Core AI Stack
- **Ollama**: Local AI model for generating embeddings and processing
- **ChromaDB**: Vector database for storing and searching video embeddings
- **FastAPI**: RESTful API endpoints for recommendations
- **SQLAlchemy**: Database ORM for user history and preferences

### Models
- **Primary Model**: `llama3.2:3b` (lightweight, fast, suitable for embeddings)
- **Fallback**: Simple text-based features if Ollama is unavailable

## 📁 Project Structure

```
ai/
├── __init__.py                    # AI module initialization
├── models/
│   ├── __init__.py
│   └── video_embedding.py        # ChromaDB + Ollama integration
├── services/
│   ├── __init__.py
│   └── recommendation_service.py  # Core recommendation logic
└── routes/
    ├── __init__.py
    └── ai_routes.py              # API endpoints

video/
├── __init__.py                   # Video module initialization
├── models/
│   ├── __init__.py
│   └── video_models.py          # Database models
├── repositories/
│   ├── __init__.py
│   └── video_repository.py      # Data access layer
├── services/
│   ├── __init__.py
│   └── video_service.py         # Business logic
├── routes/
│   ├── __init__.py
│   └── video_routes.py          # Video API endpoints
└── schemas/
    └── __init__.py              # Pydantic schemas
```

## 🧠 Recommendation Strategies

### 1. Content-Based Filtering
- **How it works**: Analyzes video content (title, description, tags, category)
- **Technology**: Ollama generates embeddings, ChromaDB finds similar vectors
- **Use case**: "Similar to videos you enjoyed"

### 2. Collaborative Filtering
- **How it works**: Finds users with similar viewing patterns
- **Technology**: Jaccard similarity on user-video interactions
- **Use case**: "Users with similar taste also liked"

### 3. Category-Based Recommendations
- **How it works**: Recommends from user's favorite categories
- **Technology**: Statistical analysis of viewing history
- **Use case**: "From your favorite category: Technology"

### 4. Trending/Popular Videos
- **How it works**: Recommends currently popular content
- **Technology**: View count with recency weighting
- **Use case**: "Trending now"

## 📊 User History Tracking

### Tracked Metrics
- **Watch Duration**: How long user watched each video
- **Completion Percentage**: Percentage of video completed
- **Ratings**: 1-5 star ratings (optional)
- **Likes/Dislikes**: Binary feedback (optional)
- **View Timestamps**: When videos were watched

### Database Schema
```sql
-- User video history
CREATE TABLE user_video_history (
    id INTEGER PRIMARY KEY,
    user_id VARCHAR,
    video_id INTEGER,
    watched_at TIMESTAMP,
    watch_duration FLOAT,
    completion_percentage FLOAT,
    rating INTEGER,
    liked BOOLEAN
);

-- User preferences
CREATE TABLE user_preferences (
    id INTEGER PRIMARY KEY,
    user_id VARCHAR UNIQUE,
    preferred_categories TEXT,  -- JSON array
    disliked_categories TEXT,   -- JSON array
    preferred_duration_min FLOAT,
    preferred_duration_max FLOAT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

## 🔧 Setup Instructions

### Prerequisites
1. **Python 3.8+**
2. **Ollama** installed and running
3. **ChromaDB** (installed via pip)

### Quick Setup
```bash
# For Linux/Mac
chmod +x setup_ai.sh
./setup_ai.sh

# For Windows
setup_ai.bat
```

### Manual Setup
```bash
# 1. Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# 2. Start Ollama
ollama serve

# 3. Pull the model
ollama pull llama3.2:3b

# 4. Install Python dependencies
pip install ollama chromadb numpy

# 5. Start the server
python main.py
```

## 🔌 API Endpoints

### Get Recommendations
```http
GET /api/ai/recommendations
Authorization: Bearer <token>
```

**Parameters:**
- `limit` (int): Number of recommendations (1-50)
- `exclude_watched` (bool): Exclude already watched videos
- `category_id` (int): Filter by category

**Response:**
```json
{
    "success": true,
    "recommendations": [
        {
            "id": 1,
            "title": "Introduction to AI",
            "description": "Learn AI basics",
            "file_url": "https://...",
            "recommendation_score": 0.85,
            "recommendation_reason": "Similar to videos you enjoyed"
        }
    ],
    "total_count": 10,
    "strategies_used": ["content_based", "collaborative", "trending"]
}
```

### Current Video Recommendations
```http
GET /api/ai/recommendations/current-video/{video_id}
Authorization: Bearer <token>
```

### Search Recommendations
```http
GET /api/ai/search-recommendations?query=machine learning
Authorization: Bearer <token>
```

### Video History
```http
POST /api/videos/history/
Authorization: Bearer <token>
Content-Type: application/json

{
    "video_id": 1,
    "watch_duration": 300.5,
    "completion_percentage": 75.2
}
```

### Rate Video
```http
POST /api/videos/{video_id}/rate
Authorization: Bearer <token>
Content-Type: application/json

{
    "rating": 5
}
```

### Like/Dislike Video
```http
POST /api/videos/{video_id}/like
Authorization: Bearer <token>
Content-Type: application/json

{
    "liked": true
}
```

## 🛠️ Configuration

### Environment Variables
```bash
# Optional: Ollama configuration
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b

# ChromaDB configuration
CHROMA_DB_PATH=./chroma_db
```

### Recommendation Weights
```python
# In recommendation_service.py
CONTENT_BASED_WEIGHT = 0.8
COLLABORATIVE_WEIGHT = 0.6
CATEGORY_WEIGHT = 0.5
TRENDING_WEIGHT = 0.4
```

## 📈 Performance Optimization

### Embedding Generation
- **Batch Processing**: Process multiple videos simultaneously
- **Caching**: Cache embeddings to avoid regeneration
- **Lazy Loading**: Generate embeddings only when needed

### Database Optimization
- **Indexing**: Proper indexes on user_id, video_id, watched_at
- **Pagination**: Limit history queries to recent data
- **Connection Pooling**: Reuse database connections

### AI Model Optimization
- **Model Size**: Use lightweight models (3B parameters)
- **Quantization**: Enable model quantization for faster inference
- **Parallel Processing**: Process multiple requests concurrently

## 🧪 Testing

### Health Check
```bash
curl http://localhost:8000/api/ai/health
```

### Test Recommendations
```bash
# Get recommendations for a user
curl -H "Authorization: Bearer <token>" \
     http://localhost:8000/api/ai/recommendations

# Search for videos
curl -H "Authorization: Bearer <token>" \
     http://localhost:8000/api/ai/search-recommendations?query=tutorial
```

## 🔍 Monitoring

### System Stats
```http
GET /api/ai/stats
Authorization: Bearer <token>
```

**Response:**
```json
{
    "embedding_stats": {
        "total_videos": 1500,
        "collection_name": "video_embeddings",
        "model": "llama3.2:3b"
    },
    "total_users_with_history": 250,
    "total_interactions": 5000,
    "recommendation_engine": "Ollama + ChromaDB"
}
```

### Logs
```bash
# Check application logs
tail -f logs/app.log

# Check Ollama logs
ollama logs
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Ollama Not Running
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama
ollama serve
```

#### 2. Model Not Found
```bash
# Pull the required model
ollama pull llama3.2:3b

# Check available models
ollama list
```

#### 3. ChromaDB Issues
```bash
# Clear ChromaDB cache
rm -rf ./chroma_db

# Rebuild embeddings
curl -X POST -H "Authorization: Bearer <token>" \
     http://localhost:8000/api/ai/embeddings/rebuild
```

#### 4. Poor Recommendations
- **Insufficient Data**: Need more user interactions
- **Cold Start**: New users need to rate/watch videos
- **Category Imbalance**: Ensure diverse video categories

### Performance Issues
- **Slow Embeddings**: Use smaller model or enable quantization
- **High Memory Usage**: Limit batch size and enable garbage collection
- **Database Bottlenecks**: Add indexes and optimize queries

## 🚀 Deployment

### Docker
```dockerfile
# Add to Dockerfile
RUN curl -fsSL https://ollama.ai/install.sh | sh
RUN ollama pull llama3.2:3b
EXPOSE 11434
```

### Production Considerations
- **Load Balancing**: Distribute AI requests across multiple instances
- **Caching**: Use Redis for frequently accessed recommendations
- **Monitoring**: Set up alerts for AI service health
- **Backup**: Regular backup of ChromaDB and user data

## 📚 Further Reading

- [Ollama Documentation](https://ollama.ai/docs)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Recommendation Systems Theory](https://en.wikipedia.org/wiki/Recommender_system)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Ensure AI components are properly tested
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
