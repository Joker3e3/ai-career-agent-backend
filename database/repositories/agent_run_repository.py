from datetime import datetime

from sqlalchemy.orm import Session

from database.database import SessionLocal
from database.models.agent_run import AgentRun


def create_agent_run(
    db: Session,
    workflow_id: str,
    user_id: str,
    run_type: str,
    status: str,
    input_summary: str,
    jd_text: str,
    match_score: int | None,
    final_report: str | None = None,
    started_at: datetime | None = None,
    session_id: str | None = None,
    resume_text: str | None = None,
    checkpoint_version: int = 1,
):
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
        session_id=session_id,
        resume_text=resume_text,
        checkpoint_version=checkpoint_version
    )

    db.add(agent_run)
    db.flush()
    db.refresh(agent_run)

    return agent_run


def get_agent_run_by_workflow_id(
    workflow_id: str,
):
    db = SessionLocal()

    try:
        return db.query(AgentRun).filter(AgentRun.workflow_id == workflow_id).first()

    finally:
        db.close()


def update_agent_run(
    db: Session,
    workflow_id: str,
    **updates,
):

    agent_run = db.query(AgentRun).filter(AgentRun.workflow_id == workflow_id).first()

    if not agent_run:
        return None

    for key, value in updates.items():
        setattr(agent_run, key, value)

    db.flush()
    db.refresh(agent_run)

    return agent_run


def list_agent_runs_by_user(
    user_id: str,
    limit: int = 50,
):
    db = SessionLocal()

    try:
        return (
            db.query(AgentRun)
            .filter(AgentRun.user_id == user_id)
            .order_by(AgentRun.created_at.desc())
            .limit(limit)
            .all()
        )

    finally:
        db.close()
