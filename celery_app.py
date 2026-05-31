from celery import Celery

from config.settings import REDIS_HOST, REDIS_PORT

CELERY_BROKER_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"
CELERY_RESULT_BACKEND = f"redis://{REDIS_HOST}:{REDIS_PORT}/1"

celery_app = Celery(
    "ai_career_agent",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_track_started=True,
    timezone="Asia/Shanghai",
    enable_utc=False,
)

# celery_app.autodiscover_tasks(["tasks"])
celery_app.conf.imports = ("tasks.career_analysis_task",)
