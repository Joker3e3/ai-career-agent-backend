from celery import Celery

from config.logging import setup_logging

setup_logging()
from config.settings import REDIS_HOST, REDIS_PORT
from tools import register_all_tools

CELERY_BROKER_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"
CELERY_RESULT_BACKEND = f"redis://{REDIS_HOST}:{REDIS_PORT}/1"
CELERY_QUEUE_NAME = "celery"

celery_app = Celery(
    "ai_career_agent",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
)

register_all_tools()

celery_app.conf.update(
    task_track_started=True,
    timezone="Asia/Shanghai",
    enable_utc=False,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_default_queue=CELERY_QUEUE_NAME,
)

# celery_app.autodiscover_tasks(["tasks"])
celery_app.conf.imports = ("tasks.career_analysis_task",)
