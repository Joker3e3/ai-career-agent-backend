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
    "load_memory": lambda state: {
        "user_id": state.get("user_id"),
        "session_id": state.get("session_id"),
    },
    "analyze_jd": lambda state: {
        "job_description_preview": preview_text(
            state.get("job_description"),
            500,
        ),
        "job_description_length": len(state.get("job_description", "")),
    },
    "plan_career_analysis": lambda state: {
        "role_title": state.get("jd_analysis", {}).get("role_title", ""),
        "role_category": state.get("jd_analysis", {}).get("role_category", ""),
        "requirements_count": len(state.get("jd_analysis", {}).get("requirements", [])),
        "requirements_preview": [
            {
                "dimension": item.get("dimension", ""),
                "priority": item.get("priority", ""),
                "keywords": item.get("keywords", [])[:5],
            }
            for item in state.get("jd_analysis", {}).get("requirements", [])[:5]
        ],
    },
    "build_retrieval_queries": lambda state: {
        "retrieval_dimensions_count": len(
            state.get("execution_plan", {}).get("retrieval_dimensions", [])
        ),
        "retrieval_dimensions_preview": [
            {
                "dimension": item.get("dimension", ""),
                "priority": item.get("priority", ""),
                "keywords": item.get("keywords", [])[:5],
            }
            for item in state.get("execution_plan", {}).get("retrieval_dimensions", [])[
                :5
            ]
        ],
    },
    "retrieve_resume_evidence": lambda state: {
        "query_count": len(state.get("query_plan", {}).get("queries", [])),
        "queries_preview": [
            {
                "dimension": item.get("dimension", ""),
                "query": preview_text(item.get("query", ""), 200),
                "keywords": item.get("keywords", [])[:5],
            }
            for item in state.get("query_plan", {}).get("queries", [])[:5]
        ],
    },
    "reflect_evidence": lambda state: {
        "retrieval_dimensions_count": len(
            state.get("execution_plan", {}).get("retrieval_dimensions", [])
        ),
        "query_count": len(state.get("query_plan", {}).get("queries", [])),
        "skill_evidence_count": len(state.get("skill_evidence", [])),
        "background_evidence_count": len(state.get("background_evidence", [])),
        "evidence_preview": [
            preview_text(item.get("content", ""), 300)
            for item in (
                state.get("skill_evidence", []) + state.get("background_evidence", [])
            )[:3]
        ],
        "available_tools": [
            item.get("name") for item in state.get("available_tools", [])
        ],
        "retry_count": state.get("retry_count", 0),
        "max_retry": state.get("max_retry", 1),
    },
    "execute_react_action": lambda state: {
        "decision": state.get("react_decision", {}).get("decision"),
        "thought": preview_text(
            state.get("react_decision", {}).get("thought", ""),
            300,
        ),
        "tool_name": state.get("react_decision", {}).get("tool_name"),
        "tool_input": state.get("react_decision", {}).get("tool_input"),
        "retry_count": state.get("retry_count", 0),
        "max_retry": state.get("max_retry", 1),
    },
    # Deprecated:
    # 旧版固定 retry 节点，当前 graph 不再连接。
    # 保留 input builder 仅用于历史兼容。
    "retry_retrieve_evidence": lambda state: {
        "deprecated": True,
        "reason": "旧版固定 retry 逻辑，已被 ReactDecision + execute_react_action 替代。",
        "retry_count": state.get("retry_count", 0),
    },
    "extract_resume_profile": lambda state: {
        "skill_evidence_count": len(state.get("skill_evidence", [])),
        "background_evidence_count": len(state.get("background_evidence", [])),
        "evidence_preview": [
            preview_text(item.get("content", ""), 300)
            for item in (
                state.get("skill_evidence", []) + state.get("background_evidence", [])
            )[:3]
        ],
    },
    "match_job": lambda state: {
        "role_title": state.get("jd_analysis", {}).get("role_title", ""),
        "role_category": state.get("jd_analysis", {}).get("role_category", ""),
        "requirements_count": len(state.get("jd_analysis", {}).get("requirements", [])),
        "resume_profile_keys": list(state.get("resume_profile", {}).keys()),
    },
    "generate_learning_plan": lambda state: {
        "match_score": state.get("match_result", {}).get("match_score"),
        "missing_skills": state.get("match_result", {}).get("missing_skills", []),
        "application_history_count": len(state.get("application_history", [])),
        "profile_summary_preview": preview_text(
            state.get("profile_summary", ""),
            300,
        ),
        "preference_preview": preview_text(
            state.get("preference", ""),
            300,
        ),
    },
    "generate_interview_tips": lambda state: {
        "match_score": state.get("match_result", {}).get("match_score"),
        "missing_skills": state.get("match_result", {}).get("missing_skills", []),
        "risks": state.get("match_result", {}).get("risks", []),
        "application_history_count": len(state.get("application_history", [])),
        "profile_summary_preview": preview_text(
            state.get("profile_summary", ""),
            300,
        ),
        "preference_preview": preview_text(
            state.get("preference", ""),
            300,
        ),
    },
    "generate_cover_letter": lambda state: {
        "role_title": state.get("jd_analysis", {}).get("role_title", ""),
        "match_score": state.get("match_result", {}).get("match_score"),
        "strengths": state.get("match_result", {}).get("strengths", []),
        "application_history_count": len(state.get("application_history", [])),
        "profile_summary_preview": preview_text(
            state.get("profile_summary", ""),
            300,
        ),
        "preference_preview": preview_text(
            state.get("preference", ""),
            300,
        ),
    },
    "generate_report": lambda state: {
        "match_result": state.get("match_result"),
        "learning_plan_preview": preview_text(
            state.get("learning_plan"),
            300,
        ),
        "interview_tips_preview": preview_text(
            state.get("interview_tips"),
            300,
        ),
        "cover_letter_preview": preview_text(
            state.get("cover_letter"),
            300,
        ),
    },
    "save_memory": lambda state: {
        "user_id": state.get("user_id"),
        "workflow_id": state.get("workflow_id"),
        "role_title": state.get("jd_analysis", {}).get("role_title", ""),
        "match_score": state.get("match_result", {}).get("match_score"),
        "final_report_preview": preview_text(
            state.get("final_report"),
            500,
        ),
    },
    "create_confirmation": lambda state: {
        "match_score": state.get("match_result", {}).get("match_score"),
        "cover_letter_preview": preview_text(
            state.get("cover_letter"),
            500,
        ),
        "final_report_preview": preview_text(
            state.get("final_report"),
            500,
        ),
    },
}


def build_node_input_summary(node_name: str, state: dict) -> str | None:
    builder = NODE_INPUT_BUILDERS.get(node_name)

    if not builder:
        return None

    return to_json_summary(builder(state))
