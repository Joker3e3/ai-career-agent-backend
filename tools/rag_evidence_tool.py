import os
import requests


RAG_SERVICE_URL = os.getenv(
    "RAG_SERVICE_URL",
    "http://127.0.0.1:8000"
)


def retrieve_evidence_from_rag(
    user_id: str,
    query: str
) -> list[dict]:
    url = f"{RAG_SERVICE_URL}/retrieve_evidence"

    payload = {
        "user_id": user_id,
        "question": query
    }

    response = requests.post(
        url,
        json=payload,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    return data.get("evidence", [])