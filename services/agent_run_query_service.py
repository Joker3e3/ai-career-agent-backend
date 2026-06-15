import logging
import json

from fastapi import HTTPException

from constants.workflow_status import WorkflowStatus
from database.database import SessionLocal
from database.repositories.agent_run_repository import (
    get_agent_run_by_workflow_id,
    list_agent_runs_by_user,
    update_agent_run,
)
from database.repositories.human_confirmation_repository import (
    get_latest_confirmation_by_workflow_id,
)

logger = logging.getLogger(__name__)


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
    input_summary = agent_run.input_summary
    candidate_id = ""
    resume_id = ""

    try:
        if input_summary:
            input_summary_data = json.loads(input_summary)

            if isinstance(input_summary_data, dict):
                candidate_id = input_summary_data.get("candidate_id", "")
                resume_id = input_summary_data.get("resume_id", "")

    except json.JSONDecodeError:
        # 兼容旧数据：以前 input_summary 可能只是普通 JD 文本，不是 JSON
        candidate_id = ""
        resume_id = ""

    return {
        "workflow_id": agent_run.workflow_id,
        "user_id": agent_run.user_id,
        "run_type": agent_run.run_type,
        "status": agent_run.status,
        "jd_text": agent_run.jd_text,
        "input_summary": agent_run.input_summary,
        "candidate_id": candidate_id,
        "resume_id": resume_id,
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
            "jd_text": run.jd_text,
            "created_at": run.created_at,
            "updated_at": run.updated_at,
        }
        for run in runs
    ]

def cancel_agent_run(workflow_id: str):
    agent_run = get_agent_run_by_workflow_id(
        workflow_id=workflow_id,
    )

    if not agent_run:
        raise HTTPException(
            status_code=404,
            detail="workflow 不存在",
        )

    if agent_run.status not in [WorkflowStatus.RUNNING, WorkflowStatus.QUEUED, WorkflowStatus.WAITING_HUMAN_CONFIRMATION]:
        raise HTTPException(
            status_code=400,
            detail="只能取消 running 或 queued 或 waiting_human_confirmation 状态的 workflow",
        )
    db = SessionLocal()
    
    try:
        if agent_run.status == WorkflowStatus.RUNNING:
            next_status = WorkflowStatus.CANCELLING
            update_agent_run(
                db=db,
                workflow_id=workflow_id,
                status=WorkflowStatus.CANCELLING,
            )
        else:
            next_status = WorkflowStatus.CANCELLED
            update_agent_run(
                db=db,
                workflow_id=workflow_id,
                status=WorkflowStatus.CANCELLED,
            )
        db.commit()
    finally:
        db.close()

    return {
        "workflow_id": workflow_id,
        "status": next_status,
    }