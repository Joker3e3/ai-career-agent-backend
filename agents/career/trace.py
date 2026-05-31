from functools import wraps

from app.constants.workflow_status import AgentStepStatus
from app.database.repositories.agent_step_repository import (
    create_agent_step,
    update_agent_step,
)
from app.database.repositories.tool_call_repository import (
    create_tool_call,
    update_tool_call,
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
                workflow_id=workflow_id, node_name=node_name, started_at=start_time
            )
            state["_current_step_id"] = step.id

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
            finally:
                state.pop("_current_step_id", None)

        return wrapper

    return decorator


def trace_tool(
    tool_name: str,
    tool_type: str,
):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            workflow_id = kwargs.get("workflow_id")
            step_id = kwargs.get("step_id")

            if not workflow_id:
                return func(*args, **kwargs)

            start_time = now_utc8()

            tool_call = create_tool_call(
                workflow_id=workflow_id,
                step_id=step_id,
                tool_name=tool_name,
                tool_type=tool_type,
                started_at=start_time,
                input_summary=str(
                    {
                        "args": args,
                        "kwargs": {
                            key: value
                            for key, value in kwargs.items()
                            if key not in {"workflow_id", "step_id"}
                        },
                    }
                )[:1000],
            )

            try:
                result = func(*args, **kwargs)

                end_time = now_utc8()
                duration_ms = int((end_time - start_time).total_seconds() * 1000)

                update_tool_call(
                    tool_call_id=tool_call.id,
                    status=AgentStepStatus.SUCCESS.value,
                    ended_at=end_time,
                    duration_ms=duration_ms,
                    output_summary=str(result)[:1000],
                )

                return result

            except Exception as exc:
                end_time = now_utc8()
                duration_ms = int((end_time - start_time).total_seconds() * 1000)

                update_tool_call(
                    tool_call_id=tool_call.id,
                    status=AgentStepStatus.FAILED.value,
                    ended_at=end_time,
                    duration_ms=duration_ms,
                    error_message=str(exc),
                )

                raise

        return wrapper

    return decorator
