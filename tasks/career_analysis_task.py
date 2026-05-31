from celery_app import celery_app

from services.career_analysis_service import execute_career_analysis_workflow


@celery_app.task
def test_task():
    print("Celery task running")

    return {"success": True}


@celery_app.task
def execute_career_analysis_task(
    workflow_id: str,
    user_id: str,
    session_id: str,
    job_description: str,
    resume_text: str,
):
    return execute_career_analysis_workflow(
        workflow_id=workflow_id,
        user_id=user_id,
        session_id=session_id,
        job_description=job_description,
        resume_text=resume_text,
    )
