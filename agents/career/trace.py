from functools import wraps

from app.constants.workflow_status import AgentStepStatus
from app.database.repositories.agent_step_repository import (
    create_agent_step,
    update_agent_step,
)
from app.utils.time import now_utc8


def trace_node(node_name: str):
    def decorator(func):
        @wraps(func)
        def wrapper(state, *args, **kwargs):
            workflow_id = state.get("workflow_id")

            if not workflow_id:
                return func(state, *args, **kwargs)

            start_time = now_utc8()

            step = create_agent_step(
                workflow_id=workflow_id,
                node_name=node_name,
                started_at=start_time
            )

            try:
                result = func(state, *args, **kwargs)

                end_time = now_utc8()
                duration_ms = int((end_time - start_time).total_seconds() * 1000)

                update_agent_step(
                    step_id=step.id,
                    status=AgentStepStatus.SUCCESS.value,
                    ended_at=end_time,
                    duration_ms=duration_ms,
                    output_summary=str(result)[:1000],
                )

                return result

            except Exception as exc:
                end_time = now_utc8()
                duration_ms = int((end_time - start_time).total_seconds() * 1000)

                update_agent_step(
                    step_id=step.id,
                    status=AgentStepStatus.FAILED.value,
                    ended_at=end_time,
                    duration_ms=duration_ms,
                    error_message=str(exc),
                )

                raise

        return wrapper

    return decorator
