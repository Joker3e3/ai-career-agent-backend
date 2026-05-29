from app.database.database import SessionLocal
from app.database.models.agent_run import AgentRun


def create_agent_run(
    workflow_id: str,
    user_id: str,
    status: str,
    jd_text: str,
    final_report: str,
):
    db = SessionLocal()

    try:
        agent_run = AgentRun(
            workflow_id=workflow_id,
            user_id=user_id,
            status=status,
            jd_text=jd_text,
            final_report=final_report,
        )

        db.add(agent_run)
        db.commit()
        db.refresh(agent_run)

        return agent_run

    finally:
        db.close()


def get_agent_run_by_workflow_id(
    workflow_id: str,
):
    db = SessionLocal()

    try:
        return (
            db.query(AgentRun)
            .filter(
                AgentRun.workflow_id == workflow_id
            )
            .first()
        )

    finally:
        db.close()


def update_agent_run(
    workflow_id: str,
    **updates,
):
    db = SessionLocal()

    try:
        agent_run = (
            db.query(AgentRun)
            .filter(
                AgentRun.workflow_id == workflow_id
            )
            .first()
        )

        if not agent_run:
            return None

        for key, value in updates.items():
            setattr(agent_run, key, value)

        db.commit()
        db.refresh(agent_run)

        return agent_run

    finally:
        db.close()