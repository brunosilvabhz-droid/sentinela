from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "sentinela",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.workers.tasks"],
)

celery_app.conf.beat_schedule = {
    "dispatch-due-alerts-every-minute": {
        "task": "app.workers.tasks.dispatch_due_alerts",
        "schedule": 60.0,
    },
    "purge-ingestion-data-daily": {
        "task": "app.workers.tasks.purge_ingestion_data",
        "schedule": 86400.0,
    },
}
celery_app.conf.timezone = "UTC"
celery_app.conf.worker_prefetch_multiplier = 1
celery_app.conf.task_acks_late = True
celery_app.conf.worker_max_tasks_per_child = 20
celery_app.conf.worker_max_memory_per_child = 180000
