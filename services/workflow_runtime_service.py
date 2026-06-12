import logging

from constants.workflow_status import WorkflowStatus
from database.repositories.agent_run_repository import get_agent_run_by_workflow_id
from exceptions.workflow_exceptions import WorkflowCancelledException

logger = logging.getLogger(__name__)
def check_workflow_cancelled(workflow_id: str):
    agent_run = get_agent_run_by_workflow_id(
        workflow_id=workflow_id,
    )

    if not agent_run:
        return

    if agent_run.status == WorkflowStatus.CANCELLING:
        logger.info("当前workflow已被用户中止，node退出: workflow_id=%s, current_status=%s", workflow_id, agent_run.status)
        raise WorkflowCancelledException(
            f"workflow {workflow_id} 已被用户取消"
        )