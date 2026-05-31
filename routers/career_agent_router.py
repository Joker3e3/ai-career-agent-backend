from fastapi import APIRouter

from services.agent_trace_service import get_workflow_trace
from services.agent_run_query_service import get_agent_run_detail

router = APIRouter()


@router.get("/career_agent/runs/{workflow_id}/trace")
async def get_trace(workflow_id: str):
    return get_workflow_trace(workflow_id)


@router.get("/career_agent/runs/{workflow_id}")
async def get_run_detail(workflow_id: str):
    return get_agent_run_detail(workflow_id)
