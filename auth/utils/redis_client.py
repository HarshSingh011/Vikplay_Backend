"""
Redis client configuration and utilities
"""
import os
import redis
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class RedisClient:
    """Redis client singleton"""
    
    _instance: Optional[redis.Redis] = None
    
    @classmethod
    def get_client(cls) -> redis.Redis:
        """Get or create Redis client instance"""
        if cls._instance is None:
            redis_host = os.getenv("REDIS_HOST", "localhost")
            redis_port = int(os.getenv("REDIS_PORT", "6379"))
            redis_db = int(os.getenv("REDIS_DB", "0"))
            redis_password = os.getenv("REDIS_PASSWORD", None)
            
            cls._instance = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                password=redis_password,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            
            # Test connection
            try:
                cls._instance.ping()
                print("✅ Redis connected successfully")
            except redis.ConnectionError as e:
                print(f"❌ Redis connection failed: {e}")
                print("⚠️ Falling back to database-only mode")
                cls._instance = None
        
        return cls._instance
    
    @classmethod
    def is_available(cls) -> bool:
        """Check if Redis is available"""
        try:
            client = cls.get_client()
            if client:
                client.ping()
                return True
        except:
            pass
        return False


# Global Redis client instance
def get_redis() -> Optional[redis.Redis]:
    """Get Redis client if available"""
    try:
        return RedisClient.get_client()
    except:
        return None
