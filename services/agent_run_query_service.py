from fastapi import HTTPException

from database.database import SessionLocal
from database.repositories.agent_run_repository import (
    get_agent_run_by_workflow_id,
    list_agent_runs_by_user,
)
from database.repositories.human_confirmation_repository import (
    get_latest_confirmation_by_workflow_id,
)


def get_agent_run_detail(workflow_id: str):

    agent_run = get_agent_run_by_workflow_id(
        workflow_id=workflow_id,
    )

    if not agent_run:
        raise HTTPException(
            status_code=404,
            detail="workflow 不存在",
        )

    confirmation = get_latest_confirmation_by_workflow_id(
        workflow_id=workflow_id,
    )

    return {
        "workflow_id": agent_run.workflow_id,
        "user_id": agent_run.user_id,
        "run_type": agent_run.run_type,
        "status": agent_run.status,
        "input_summary": agent_run.input_summary,
        "match_score": agent_run.match_score,
        "final_report": agent_run.final_report,
        "error_message": agent_run.error_message,
        "created_at": agent_run.created_at,
        "started_at": agent_run.started_at,
        "completed_at": agent_run.completed_at,
        "confirmation": (
            None
            if not confirmation
            else {
                "confirmation_id": confirmation.confirmation_id,
                "status": confirmation.status,
                "user_action": confirmation.user_action,
                "message": confirmation.message,
                "payload_snapshot": confirmation.payload_snapshot,
                "created_at": confirmation.created_at,
                "updated_at": confirmation.updated_at,
            }
        ),
    }


def get_user_agent_runs(
    user_id: str,
    limit: int = 50
):
    runs = list_agent_runs_by_user(user_id, limit=limit)

    return [
        {
            "workflow_id": run.workflow_id,
            "status": run.status,
            "input_summary": run.input_summary,
            "created_at": run.created_at,
            "updated_at": run.updated_at,
        }
        for run in runs
    ]
