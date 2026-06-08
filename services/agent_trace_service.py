from database.database import SessionLocal
from database.repositories.agent_step_repository import (
    list_agent_steps_by_workflow_id,
)
from database.repositories.tool_call_repository import (
    list_tool_calls_by_workflow_id,
)


def get_workflow_trace(workflow_id: str):

    steps = list_agent_steps_by_workflow_id(workflow_id=workflow_id)

    tool_calls = list_tool_calls_by_workflow_id(workflow_id=workflow_id)

    tool_calls_by_step_id: dict[int, list] = {}

    for tool_call in tool_calls:
        if tool_call.step_id is None:
            continue

        tool_calls_by_step_id.setdefault(
            tool_call.step_id,
            [],
        ).append(tool_call)

    return {
        "workflow_id": workflow_id,
        "steps": [
            {
                "id": step.id,
                "step_order": step.step_order,
                "node_name": step.node_name,
                "status": step.status,
                "input_summary": step.input_summary,
                "output_summary": step.output_summary,
                "error_message": step.error_message,
                "started_at": step.started_at,
                "ended_at": step.ended_at,
                "duration_ms": step.duration_ms,
                "input_tokens": step.input_tokens,
                "output_tokens": step.output_tokens,
                "total_tokens": step.total_tokens,
                "model_name": step.model_name,
                # "provider": step.provider,
                "tool_calls": [
                    {
                        "id": tool_call.id,
                        "tool_name": tool_call.tool_name,
                        "tool_type": tool_call.tool_type,
                        "status": tool_call.status,
                        "input_summary": tool_call.input_summary,
                        "output_summary": tool_call.output_summary,
                        "error_message": tool_call.error_message,
                        "started_at": tool_call.started_at,
                        "ended_at": tool_call.ended_at,
                        "duration_ms": tool_call.duration_ms,
                    }
                    for tool_call in tool_calls_by_step_id.get(step.id, [])
                ],
            }
            for step in steps
        ],
    }
