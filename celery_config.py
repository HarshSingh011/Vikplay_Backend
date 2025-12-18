"""
Celery configuration for async task processing
Uses Redis as message broker and result backend
"""
from celery import Celery
import os
from dotenv import load_dotenv

load_dotenv()

# Redis configuration
redis_host = os.getenv("REDIS_HOST", "localhost")
redis_port = os.getenv("REDIS_PORT", "6379")
redis_db = os.getenv("REDIS_DB", "0")
redis_password = os.getenv("REDIS_PASSWORD", "")

# Build Redis URL with optional password
if redis_password:
    redis_url = f"redis://:{redis_password}@{redis_host}:{redis_port}/{redis_db}"
else:
    redis_url = f"redis://{redis_host}:{redis_port}/{redis_db}"

# Create Celery app
celery_app = Celery(
    "vikpay",
    broker=redis_url,
    backend=redis_url,
    include=['auth.tasks.email_tasks']
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Task execution settings
    task_track_started=True,
    task_time_limit=300,  # 5 minutes max per task
    task_soft_time_limit=240,  # 4 minutes soft limit
    
    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour
    result_backend_transport_options={
        'master_name': 'mymaster',
    },
    
    # Broker settings
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,
    
    # Worker settings
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    
    # Task routing
    task_routes={
        'auth.tasks.email_tasks.*': {'queue': 'emails'},
        'auth.tasks.cleanup_tasks.*': {'queue': 'cleanup'},
    },
    
    # Beat schedule for periodic tasks
    beat_schedule={
        'cleanup-expired-otps': {
            'task': 'auth.tasks.cleanup_tasks.cleanup_expired_otps',
            'schedule': 3600.0,  # Run every hour
        },
        'cleanup-expired-sessions': {
            'task': 'auth.tasks.cleanup_tasks.cleanup_expired_sessions',
            'schedule': 1800.0,  # Run every 30 minutes
        },
    },
)

if __name__ == '__main__':
    celery_app.start()
