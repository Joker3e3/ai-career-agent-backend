from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agents.career_graph import run_career_agent

app = FastAPI()

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


class CareerAnalyzeRequest(BaseModel):
    session_id: str
    job_description: str
    resume_text: str


@app.post("/career_agent/analyze")
def analyze_career(request: CareerAnalyzeRequest):
    report = run_career_agent(
        session_id=request.session_id,
        job_description=request.job_description,
        resume_text=request.resume_text,
    )

    return {"report": report}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8010)
