from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "pc_builder",
    broker=settings.broker_url,
    backend=settings.result_backend,
    include=["app.workers.tasks"],
)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Europe/Warsaw",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
    result_expires=86400,
    task_routes={
        "app.workers.tasks.sync_store_task": {"queue": "parsers"},
        "app.workers.tasks.sync_all_stores_task": {"queue": "parsers"},
        "app.workers.tasks.cleanup_task": {"queue": "maintenance"},
        "app.workers.tasks.update_currency_rates_task": {"queue": "maintenance"},
        "app.workers.tasks.check_price_alerts_task": {"queue": "notifications"},
    },
    beat_schedule={
        "sync-active-stores-every-6-hours": {
            "task": "app.workers.tasks.sync_all_stores_task",
            "schedule": crontab(minute=15, hour="*/6"),
        },
        "update-nbp-rates-weekdays": {
            "task": "app.workers.tasks.update_currency_rates_task",
            "schedule": crontab(minute=30, hour=13, day_of_week="1-5"),
        },
        "check-price-alerts-hourly": {
            "task": "app.workers.tasks.check_price_alerts_task",
            "schedule": crontab(minute=25),
        },
        "cleanup-hourly": {
            "task": "app.workers.tasks.cleanup_task",
            "schedule": crontab(minute=5),
        },
    },
)
