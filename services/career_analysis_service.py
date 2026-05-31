import uuid

from constants.workflow_status import WorkflowStatus
from database.database import SessionLocal
from database.repositories.agent_run_repository import (
    create_agent_run,
    update_agent_run,
)
from agents.career_graph import career_graph
from utils.time import now_utc8


def submit_career_analysis(
    user_id: str,
    session_id: str,
    job_description: str,
    resume_text: str,
):
    workflow_id = f"workflow_{uuid.uuid4()}"

    db = SessionLocal()

    try:
        create_agent_run(
            db=db,
            workflow_id=workflow_id,
            user_id=user_id,
            run_type="career_analysis",
            status=WorkflowStatus.QUEUED.value,
            input_summary=job_description[:200],
            jd_text=job_description,
            match_score=None,
            started_at=None,
        )

        db.commit()

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()

    # 后续接 Celery 时，这里会变成：
    # execute_career_analysis_workflow.delay(
    #     workflow_id=workflow_id,
    #     user_id=user_id,
    #     session_id=session_id,
    #     job_description=job_description,
    #     resume_text=resume_text,
    # )

    return {
        "success": True,
        "workflow_id": workflow_id,
        "workflow_status": WorkflowStatus.QUEUED.value,
        "message": "分析任务已提交",
    }


def execute_career_analysis_workflow(
    workflow_id: str,
    user_id: str,
    session_id: str,
    job_description: str,
    resume_text: str,
):
    db = SessionLocal()

    try:
        update_agent_run(
            db=db,
            workflow_id=workflow_id,
            status=WorkflowStatus.RUNNING.value,
            started_at=now_utc8(),
        )

        db.commit()

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()

    result = career_graph.invoke(
        {
            "user_id": user_id,
            "session_id": session_id,
            "job_description": job_description,
            "resume_text": resume_text,
            "jd_analysis": {},
            "resume_profile": {},
            "match_result": {},
            "learning_plan": "",
            "interview_tips": "",
            "cover_letter": "",
            "memories": [],
            "final_report": "",
            "rag_evidence": [],
            "skill_evidence": [],
            "background_evidence": [],
            "query_plan": {},
            "reflection_result": {},
            "retry_evidence": [],
            "retry_count": 0,
            "max_retry": 1,
            "retry_added_count": 0,
            "workflow_id": workflow_id,
            "workflow_status": WorkflowStatus.RUNNING.value,
            "current_node": "",
            "confirmation_id": "",
            "confirmation_status": "",
            "confirmation_message": "",
        }
    )

    return result