from fastapi import APIRouter

from services.agent_trace_service import get_workflow_trace

router = APIRouter()

@router.get("/career_agent/runs/{workflow_id}/trace")
async def get_trace(workflow_id: str):
    return get_workflow_trace(workflow_id)