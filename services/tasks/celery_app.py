"""
Celery application configuration.
"""
from celery import Celery
from core.config import get_settings

settings = get_settings()

# Create Celery app
celery_app = Celery(
    "bluelabel_aios",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "services.tasks.file_processor",
        "services.tasks.digest_generator"  # Future task
    ]
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task execution settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Result backend settings
    result_expires=3600,  # 1 hour
    
    # Worker settings
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
    
    # Beat schedule for periodic tasks
    beat_schedule={
        "daily-digest": {
            "task": "generate_daily_digest",
            "schedule": 24 * 60 * 60,  # Daily
            "options": {"queue": "digest"}
        }
    }
)