import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from config.logging import setup_logging
from tools import register_all_tools

load_dotenv()

from agents.career_graph import run_career_agent, run_confirm_workflow
from services.career_analysis_service import (
    submit_career_analysis,
    execute_career_analysis_workflow,
)
from schemas.confirm_schema import ConfirmRequest
from routers.career_agent_router import router as career_agent_router

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI()

register_all_tools()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(career_agent_router)


class CareerAnalyzeRequest(BaseModel):
    session_id: str
    user_id: str
    job_description: str
    resume_text: str


@app.post("/career_agent/analyze")
def analyze_career(request: CareerAnalyzeRequest):

    submit_result = submit_career_analysis(
        user_id=request.user_id,
        session_id=request.session_id,
        job_description=request.job_description,
        resume_text=request.resume_text,
    )

    return submit_result


@app.post("/career_agent/confirm")
async def confirm_action(request: ConfirmRequest):

    return run_confirm_workflow(
        workflow_id=request.workflow_id,
        confirmation_id=request.confirmation_id,
        human_action=request.action.value,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8010)
