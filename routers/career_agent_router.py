from fastapi import APIRouter

from services.agent_trace_service import get_workflow_trace
from services.agent_run_query_service import cancel_agent_run, get_agent_run_detail, get_user_agent_runs

router = APIRouter()


@router.get("/career_agent/runs/{workflow_id}/trace")
async def get_trace(workflow_id: str):
    return get_workflow_trace(workflow_id)


@router.get("/career_agent/runs/{workflow_id}")
async def get_run_detail(workflow_id: str):
    return get_agent_run_detail(workflow_id)


@router.get("/career_agent/runs")
async def list_runs(
    user_id: str,
    limit: int = 50,
):
    return get_user_agent_runs(
        user_id=user_id,
        limit=limit,
    )

@router.post("/career_agent/cancel/{workflow_id}")
async def cancel_run(workflow_id: str):
    return cancel_agent_run(workflow_id)