from datetime import datetime

from app.database.database import SessionLocal
from app.database.models.agent_step import AgentStep
from app.constants.workflow_status import AgentStepStatus


def create_agent_step(
    workflow_id: str,
    node_name: str,
    started_at: datetime,
    input_summary: str | None = None,
):
    db = SessionLocal()

    try:

        max_step = (
            db.query(AgentStep.step_order)
            .filter(AgentStep.workflow_id == workflow_id)
            .order_by(AgentStep.step_order.desc())
            .first()
        )

        next_step_order = 1

        if max_step:
            next_step_order = max_step[0] + 1

        agent_step = AgentStep(
            workflow_id=workflow_id,
            node_name=node_name,
            started_at=started_at,
            step_order=next_step_order,
            status=AgentStepStatus.RUNNING.value,
            input_summary=input_summary
        )

        db.add(agent_step)
        db.commit()
        db.refresh(agent_step)

        return agent_step

    finally:
        db.close()


def update_agent_step(
    step_id: int,
    **updates,
):
    db = SessionLocal()

    try:
        agent_step = db.query(AgentStep).filter(AgentStep.id == step_id).first()

        if not agent_step:
            return None

        for key, value in updates.items():
            setattr(agent_step, key, value)

        db.commit()
        db.refresh(agent_step)

        return agent_step

    finally:
        db.close()
