from app.database.database import SessionLocal
from app.database.models.tool_call import ToolCall
from app.constants.workflow_status import AgentStepStatus


def create_tool_call(
    workflow_id: str,
    tool_name: str,
    tool_type: str,
    started_at,
    step_id: int | None = None,
    input_summary: str = "",
):
    db = SessionLocal()

    try:
        tool_call = ToolCall(
            workflow_id=workflow_id,
            step_id=step_id,
            tool_name=tool_name,
            tool_type=tool_type,
            status=AgentStepStatus.RUNNING.value,
            input_summary=input_summary,
            started_at=started_at,
        )

        db.add(tool_call)
        db.commit()
        db.refresh(tool_call)

        return tool_call

    finally:
        db.close()


def update_tool_call(
    tool_call_id: int,
    **updates,
):
    db = SessionLocal()

    try:
        tool_call = (
            db.query(ToolCall)
            .filter(ToolCall.id == tool_call_id)
            .first()
        )

        if not tool_call:
            return None

        for key, value in updates.items():
            setattr(tool_call, key, value)

        db.commit()
        db.refresh(tool_call)

        return tool_call

    finally:
        db.close()