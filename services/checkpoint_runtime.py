import json
import logging

from agents.career.state_policy import build_checkpoint_state
from constants.workflow_status import CheckpointMode, WorkflowStatus
from services.workflow_checkpoint_service import (
    workflow_checkpoint_service,
)

logger = logging.getLogger(__name__)


def save_workflow_checkpoint(
    state: dict,
    current_node: str,
    status: str = WorkflowStatus.RUNNING,
    mode: str = CheckpointMode.RECOVERY,
    extra_state: dict | None = None,
):
    updated_state = {
        **state,
        "current_node": current_node,
        "workflow_status": status,
        **(extra_state or {}),
    }

    full_state_json = json.dumps(
        updated_state,
        ensure_ascii=False
    )

    checkpoint_state = build_checkpoint_state(
        updated_state,
        mode=mode,
        current_node=current_node,
    )

    checkpoint_state = {
        **checkpoint_state,
        "current_node": current_node,
        "checkpoint_mode": mode,
    }

    checkpoint_json = json.dumps(
        checkpoint_state,
        ensure_ascii=False
    )

    logger.info(
        f"[CHECKPOINT] "
        f"node={current_node} "
        f"full={len(full_state_json)} "
        f"checkpoint={len(checkpoint_json)}"
    )

    workflow_checkpoint_service.save_checkpoint(
        workflow_id=state["workflow_id"],
        status=status,
        current_node=current_node,
        checkpoint=checkpoint_state,
    )