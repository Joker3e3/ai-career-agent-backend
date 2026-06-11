import logging
import uuid

from constants.workflow_status import WorkflowStatus
from database.database import SessionLocal
from database.repositories.agent_run_repository import (
    create_agent_run,
    update_agent_run,
)
from agents.career_graph import career_graph
from tools import tool_registry
from utils.time import now_utc8

logger = logging.getLogger(__name__)

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
            input_summary=job_description,
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

    from tasks.career_analysis_task import execute_career_analysis_task

    execute_career_analysis_task.delay(
        workflow_id=workflow_id,
        user_id=user_id,
        session_id=session_id,
        job_description=job_description,
        resume_text=resume_text,
    )

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

    available_tools = tool_registry.get_tool_summaries()
    logger.info("Available tools loaded: %s", available_tools)
    try:
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
                "execution_plan": {},
                "react_decision": {},
                "retry_evidence": [],
                "retry_count": 0,
                "max_retry": 1,
                "retry_added_count": 0,
                "checkpoint_version": 1,
                "workflow_id": workflow_id,
                "workflow_status": WorkflowStatus.RUNNING.value,
                "current_node": "",
                "confirmation_id": "",
                "confirmation_status": "",
                "confirmation_message": "",
                "available_tools": available_tools,
            }
        )

        return result
    except Exception as exc:
        logger.exception(
            "Career analysis workflow failed: workflow_id=%s",
            workflow_id,
        )

        db = SessionLocal()

        try:
            update_agent_run(
                db=db,
                workflow_id=workflow_id,
                status=WorkflowStatus.FAILED.value,
                error_message=str(exc)[:3000],
                completed_at=now_utc8(),
            )

            db.commit()

        except Exception:
            db.rollback()
            logger.exception(
                "Failed to update agent_run as failed: workflow_id=%s",
                workflow_id,
            )

        finally:
            db.close()

        raise
