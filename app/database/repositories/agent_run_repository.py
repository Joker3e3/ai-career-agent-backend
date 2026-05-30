from datetime import datetime

from app.database.database import SessionLocal
from app.database.models.agent_run import AgentRun


def create_agent_run(
    workflow_id: str,
    user_id: str,
    run_type: str,
    status: str,
    input_summary: str,
    jd_text: str,
    match_score: int | None,
    final_report: str,
    started_at: datetime | None = None,
):
    db = SessionLocal()

    try:
        agent_run = AgentRun(
            workflow_id=workflow_id,
            user_id=user_id,
            run_type=run_type,
            status=status,
            input_summary=input_summary,
            jd_text=jd_text,
            match_score=match_score,
            final_report=final_report,
            started_at=started_at,
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