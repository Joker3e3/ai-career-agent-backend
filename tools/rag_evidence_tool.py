import requests

from agents.career.trace import trace_tool
from config.settings import RAG_SERVICE_URL


@trace_tool(tool_name="resume_rag_retriever", tool_type="rag")
def retrieve_evidence_from_rag(
    user_id: str,
    query: str,
    candidate_id: str,
    resume_id: str,
    workflow_id: str | None = None,
    step_id: int | None = None,
) -> list[dict]:
    url = f"{RAG_SERVICE_URL}/retrieve_evidence"

    payload = {
        "user_id": user_id,
        "question": query,
        "candidate_id": candidate_id,
        "resume_id": resume_id
    }

    response = requests.post(url, json=payload, timeout=30)

    response.raise_for_status()

    data = response.json()

    return data.get("evidence", [])


def mcp_retrieve_evidence_from_rag(
    user_id: str,
    query: str,
    candidate_id: str,
    resume_id: str
) -> list[dict]:
    url = f"{RAG_SERVICE_URL}/retrieve_evidence"

    payload = {
        "user_id": user_id,
        "question": query,
        "candidate_id": candidate_id,
        "resume_id": resume_id
    }

    response = requests.post(url, json=payload, timeout=30)

    response.raise_for_status()

    data = response.json()

    return data.get("evidence", [])
