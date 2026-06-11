import logging
from urllib.parse import urlparse

import redis

from constants.workflow_status import AgentStepStatus, WorkflowStatus
from database.database import SessionLocal
from database.models.agent_run import AgentRun
from database.repositories.agent_step_repository import get_latest_running_agent_step, update_agent_step
from database.repositories.tool_call_repository import get_last_tool_call_by_workflow_id, update_tool_call
from tasks.career_analysis_task import execute_career_analysis_task
from celery_app import CELERY_BROKER_URL, CELERY_QUEUE_NAME
from utils.time import now_utc8


STUCK_STATUSES = {
    WorkflowStatus.QUEUED,
    WorkflowStatus.RUNNING,
}

logger = logging.getLogger(__name__)


def get_redis_client_from_broker_url():
    parsed = urlparse(CELERY_BROKER_URL)

    redis_db = int(parsed.path.lstrip("/") or 0)

    return redis.Redis(
        host=parsed.hostname,
        port=parsed.port or 6379,
        db=redis_db,
        decode_responses=True,
    )

def get_redis_pending_messages() -> list[str]:
    redis_client = get_redis_client_from_broker_url()
    return redis_client.lrange(CELERY_QUEUE_NAME, 0, -1)

def workflow_exists_in_redis_queue(
    workflow_id: str,
    redis_messages: list[str],
) -> bool:
    return any(workflow_id in message for message in redis_messages)

def run():
    db = SessionLocal()

    try:
        runs = (
            db.query(AgentRun)
            .filter(AgentRun.status.in_(STUCK_STATUSES))
            .order_by(AgentRun.created_at.asc())
            .all()
        )

        if not runs:
            logger.info("[RECOVERY] no stuck workflows")
            return
        
        redis_messages = get_redis_pending_messages()

        need_requeue = [
            item
            for item in runs
            if not workflow_exists_in_redis_queue(
                item.workflow_id,
                redis_messages,
            )
        ]

        logger.info(f"[RECOVERY] PG stuck workflows: {len(runs)}")
        logger.info(f"[RECOVERY] Redis pending messages: {len(redis_messages)}")
        logger.info(f"[RECOVERY] need requeue: {len(need_requeue)}")

        if not need_requeue:
            logger.info("[RECOVERY] nothing to requeue")
            return

        for item in need_requeue:
            logger.info(
                f"- workflow_id={item.workflow_id}, "
                f"status={item.status}"
            )

        confirm = input("Requeue these workflows? Type yes: ")

        if confirm.lower() != "yes":
            logger.info("[RECOVERY] cancelled")
            return

        for item in need_requeue:

            try:
                step = get_latest_running_agent_step(
                    item.workflow_id
                )

                execute_career_analysis_task.delay(
                    workflow_id=item.workflow_id,
                    user_id=item.user_id,
                    session_id=item.session_id,
                    job_description=item.jd_text,
                    resume_text=item.resume_text,
                )

                if step:
                    update_agent_step(
                        step_id=step.id,
                        status="failed",
                        error_message="Worker异常中断，任务已重新投递",
                        ended_at=now_utc8(),
                    )
                
                tool_call = get_last_tool_call_by_workflow_id(item.workflow_id)
                if tool_call and tool_call.status == AgentStepStatus.RUNNING:
                    update_tool_call(
                        tool_call_id=tool_call.id,
                        status="failed",
                        error_message="Worker异常中断，任务已重新投递",
                        ended_at=now_utc8(),
                    )

                logger.info(
                    f"[RECOVERY] requeued workflow_id={item.workflow_id}"
                )

            except Exception:
                logger.exception(
                    f"[RECOVERY] failed to requeue workflow_id={item.workflow_id}"
                )

        logger.info("[RECOVERY] done")

    finally:
        db.close()


if __name__ == "__main__":
    run()