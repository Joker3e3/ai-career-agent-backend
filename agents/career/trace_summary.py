import json


def to_json_summary(data: dict | None) -> str | None:
    if not data:
        return None

    return json.dumps(
        data,
        ensure_ascii=False,
        default=str,
    )[:1000]


def preview_text(text: str | None, limit: int = 300) -> str:
    if not text:
        return ""

    return text[:limit]


def preview_list(items: list, limit: int = 3) -> list:
    return items[:limit]


NODE_INPUT_BUILDERS = {
    "analyze_jd": lambda state: {
        "job_description_preview": preview_text(
            state.get("job_description"),
            500,
        ),
        "job_description_length": len(state.get("job_description", "")),
    },
    "retrieve_resume_evidence": lambda state: {
        "query_count": len(state.get("query_plan", {}).get("queries", [])),
        "queries_preview": [
            item.get("query", "")
            for item in state.get("query_plan", {}).get("queries", [])[:5]
        ],
    },
    "reflect_evidence": lambda state: {
        "skill_evidence_count": len(state.get("skill_evidence", [])),
        "background_evidence_count": len(state.get("background_evidence", [])),
        "evidence_preview": [
            item.get("content", "")[:300]
            for item in (
                state.get("skill_evidence", []) + state.get("background_evidence", [])
            )[:3]
        ],
        "retry_count": state.get("retry_count", 0),
    },
    "retry_retrieve_evidence": lambda state: {
        "need_retry": state.get("reflection_result", {}).get("need_retry"),
        "retry_queries_preview": [
            item.get("retry_query", "")
            for item in state.get("reflection_result", {}).get("retry_queries", [])[:5]
        ],
        "retry_count": state.get("retry_count", 0),
    },
    "generate_report": lambda state: {
        "match_result": state.get("match_result"),
        "learning_plan_preview": preview_text(state.get("learning_plan"), 300),
        "interview_tips_preview": preview_text(state.get("interview_tips"), 300),
        "cover_letter_preview": preview_text(state.get("cover_letter"), 300),
    },
    "create_confirmation": lambda state: {
        "match_score": state.get("match_result", {}).get("match_score"),
        "cover_letter_preview": preview_text(state.get("cover_letter"), 500),
        "final_report_preview": preview_text(state.get("final_report"), 500),
    },
}


def build_node_input_summary(node_name: str, state: dict) -> str | None:
    builder = NODE_INPUT_BUILDERS.get(node_name)

    if not builder:
        return None

    return to_json_summary(builder(state))
