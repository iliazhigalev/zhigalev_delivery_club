import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED

from src.services.package_service import compute_delivery_costs_for_unprocessed
from src.settings import settings

logger = logging.getLogger(__name__)


scheduler = AsyncIOScheduler()


async def safe_compute_delivery_costs():
    """
    Безопасная обёртка вокруг compute_delivery_costs_for_unprocessed.
    Логирует ошибки и предотвращает падение планировщика при исключении.
    """
    try:
        updated = await compute_delivery_costs_for_unprocessed()
        logger.info(f"Delivery costs updated for {updated} packages.")
    except Exception as e:
        logger.exception(f"Error while computing delivery costs: {e}")


def _on_job_event(event):
    """
    Колбэк для логирования результатов выполнения задач.
    """
    if event.exception:
        logger.error(f"Job {event.job_id} raised an exception.")
    else:
        logger.debug(f"Job {event.job_id} completed successfully.")


def start_scheduler():
    """
    Запускает APScheduler и регистрирует задачу перерасчёта стоимости доставки.
    """
    if scheduler.get_job("compute_delivery_costs"):
        logger.info("Scheduler already running, skipping duplicate start.")
        return

    scheduler.add_job(
        safe_compute_delivery_costs,
        trigger=IntervalTrigger(seconds=settings.DELIVERY_RATE_INTERVAL_SECONDS),
        id="compute_delivery_costs",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    scheduler.add_listener(_on_job_event, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

    scheduler.start()
    logger.info(
        f"Scheduler started. Delivery costs will update every "
        f"{settings.DELIVERY_RATE_INTERVAL_SECONDS} seconds."
    )


async def run_once_now():
    """
    Вспомогательная функция для ручного запуска перерасчёта.
    Используется при инициализации приложения или отладке.
    """
    logger.info("Running compute_delivery_costs_for_unprocessed() manually...")
    await safe_compute_delivery_costs()
