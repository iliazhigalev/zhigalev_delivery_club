from celery import Celery
from src.settings import settings
from .calculating_cost_parcel import calculating_cost_unprocessed_parcels
from celery.schedules import crontab

celery_app = Celery(
    "celery_app",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.autodiscover_tasks(["src.tasks"])

celery_app.conf.beat_schedule = {
    "run-every-5-minutes": {
        "task": "src.tasks.celery_worker.calculating_cost_unprocessed_parcels_task",
        "schedule": crontab(minute="*/5"),
    },
}
celery_app.conf.timezone = "UTC"


@celery_app.task(
    name="src.tasks.celery_worker.calculating_cost_unprocessed_parcels_task"
)
def calculating_cost_unprocessed_parcels_task():
    return calculating_cost_unprocessed_parcels()
