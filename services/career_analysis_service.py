import logging
import uuid
import json

from constants.workflow_status import CheckpointMode, WorkflowStatus
from database.database import SessionLocal
from database.repositories.agent_run_repository import (
    create_agent_run,
    get_agent_run_by_workflow_id,
    update_agent_run,
)
from agents.career_graph import RESUME_NEXT_NODE, career_graph
from exceptions.workflow_exceptions import WorkflowCancelledException
from services.workflow_checkpoint_service import workflow_checkpoint_service
from tools import tool_registry
from utils.time import now_utc8

logger = logging.getLogger(__name__)

def build_initial_state(
    workflow_id: str,
    user_id: str,
    session_id: str,
    job_description: str,
    resume_text: str,
    available_tools: list[dict],
    candidate_id: str,
    resume_id: str,
) -> dict:
    """
    构建职业分析工作流的初始状态
    """
    return {
        "user_id": user_id,
        "session_id": session_id,
        "job_description": job_description,
        "resume_text": resume_text,
        "candidate_id": candidate_id,
        "resume_id": resume_id,
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

def build_initial_or_resume_state(
    workflow_id: str,
    user_id: str,
    session_id: str,
    job_description: str,
    resume_text: str,
    available_tools: list[dict],
    candidate_id: str,
    resume_id: str,
) -> dict:
    """
    构建职业分析工作流的初始状态或从checkpoint恢复状态
    """
    checkpoint = workflow_checkpoint_service.get_checkpoint(workflow_id)

    if not checkpoint:
        return build_initial_state(
            workflow_id=workflow_id,
            user_id=user_id,
            session_id=session_id,
            job_description=job_description,
            resume_text=resume_text,
            available_tools=available_tools,
            candidate_id=candidate_id,
            resume_id=resume_id,
        )

    checkpoint_mode = checkpoint.get("checkpoint_mode", CheckpointMode.RECOVERY)
    if checkpoint_mode == CheckpointMode.CONFIRMATION:
        return {
            **checkpoint,
            "resume_skip_invoke": True,
        }

    current_node = checkpoint.get("current_node")

    resume_from_node = RESUME_NEXT_NODE.get(current_node)

    if resume_from_node is None:
        raise ValueError(
            f"Unsupported checkpoint node: {current_node}"
        )

    logger.info("\n====== route_resume: 从检查点恢复workflow ====== workflow_id=%s, current_node=%s, resume_from_node=%s",
        workflow_id, current_node, resume_from_node
    )

    return {
        **checkpoint,
        "workflow_id": workflow_id,
        "user_id": user_id,
        "session_id": session_id,
        "job_description": job_description,
        "resume_text": resume_text,
        "available_tools": available_tools,
        "workflow_status": WorkflowStatus.RUNNING.value,
        "resume_from_node": resume_from_node,
        "candidate_id": candidate_id,
        "resume_id": resume_id,
    }

def submit_career_analysis(
    user_id: str,
    session_id: str,
    candidate_id: str,
    resume_id: str,
    job_description: str,
    resume_text: str,
    checkpoint_version: int = 1,
):
    workflow_id = f"workflow_{uuid.uuid4()}"

    input_summary = json.dumps(
        {
            "candidate_id": candidate_id,
            "resume_id": resume_id,
            "job_description_preview": job_description[:300],
        },
        ensure_ascii=False,
    )
    db = SessionLocal()

    try:
        create_agent_run(
            db=db,
            workflow_id=workflow_id,
            user_id=user_id,
            run_type="career_analysis",
            status=WorkflowStatus.QUEUED.value,
            input_summary=input_summary,
            jd_text=job_description,
            match_score=None,
            started_at=None,
            session_id=session_id,
            resume_text=resume_text,
            checkpoint_version=checkpoint_version,
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
        candidate_id=candidate_id,
        resume_id=resume_id,
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
    candidate_id: str,
    resume_id: str,
):
    agent_run = get_agent_run_by_workflow_id(workflow_id=workflow_id)
    if agent_run and agent_run.status == WorkflowStatus.CANCELLED:
        logger.info("workflow already cancelled, skip execution: %s", workflow_id)
        return {
            "workflow_id": workflow_id,
            "status": WorkflowStatus.CANCELLED.value,
            "message": "workflow 已取消，跳过执行",
        }
    
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
    initial_state = build_initial_or_resume_state(
        workflow_id=workflow_id,
        user_id=user_id,
        session_id=session_id,
        job_description=job_description,
        resume_text=resume_text,
        available_tools=available_tools,
        candidate_id=candidate_id,
        resume_id=resume_id,
    )

    # 如果状态来自checkpoint且当前节点是create_confirmation，则直接返回状态，不执行workflow
    if initial_state.get("resume_skip_invoke"):
        return initial_state
    
    try:
        result = career_graph.invoke(initial_state)

        return result
    except WorkflowCancelledException as exc:
        logger.info(
            "Career analysis workflow cancelled: workflow_id=%s",
            workflow_id,
        )

        db = SessionLocal()

        try:
            update_agent_run(
                db=db,
                workflow_id=workflow_id,
                status=WorkflowStatus.CANCELLED.value,
                error_message=str(exc)[:3000],
                completed_at=now_utc8(),
            )

            db.commit()

        except Exception:
            db.rollback()
            logger.exception(
                "Failed to update agent_run as cancelled: workflow_id=%s",
                workflow_id,
            )
            raise

        finally:
            db.close()

        return {
            "workflow_id": workflow_id,
            "status": WorkflowStatus.CANCELLED.value,
            "message": "workflow 已取消",
        }
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
