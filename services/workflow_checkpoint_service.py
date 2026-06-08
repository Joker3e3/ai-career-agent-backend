from typing import Any

from database.repositories.workflow_checkpoint_repository import (
    get_workflow_checkpoint,
    update_workflow_checkpoint,
    upsert_workflow_checkpoint,
)
from services.workflow_state_service import workflow_state_service


class WorkflowCheckpointService:
    """
    Workflow checkpoint 持久化服务。

    Redis:
        用于短期快速恢复 workflow state。

    PostgreSQL:
        用于长期保存 human confirmation 阶段需要恢复的 checkpoint，
        避免 Redis TTL 过期后无法继续确认。
    """

    def save_checkpoint(
        self,
        workflow_id: str,
        status: str,
        current_node: str,
        checkpoint: dict[str, Any],
    ):
        workflow_state_service.save_state(
            workflow_id=workflow_id,
            state=checkpoint,
        )

        return upsert_workflow_checkpoint(
            workflow_id=workflow_id,
            status=status,
            current_node=current_node,
            checkpoint=checkpoint,
        )

    def get_checkpoint(
        self,
        workflow_id: str,
    ) -> dict[str, Any] | None:
        checkpoint = workflow_state_service.get_state(workflow_id)

        if checkpoint:
            return checkpoint

        return get_workflow_checkpoint(workflow_id)

    def update_checkpoint(
        self,
        workflow_id: str,
        updates: dict[str, Any],
    ) -> dict[str, Any] | None:
        checkpoint = self.get_checkpoint(workflow_id)

        if not checkpoint:
            return None

        checkpoint.update(updates)

        workflow_state_service.save_state(
            workflow_id=workflow_id,
            state=checkpoint,
        )

        update_workflow_checkpoint(
            workflow_id=workflow_id,
            checkpoint=checkpoint,
            status=checkpoint.get("workflow_status", ""),
            current_node=checkpoint.get("current_node", ""),
        )

        return checkpoint

    def mark_completed(
        self,
        workflow_id: str,
    ):
        update_workflow_checkpoint(
            workflow_id=workflow_id,
            status="completed",
        )

        workflow_state_service.delete_state(workflow_id)


workflow_checkpoint_service = WorkflowCheckpointService()