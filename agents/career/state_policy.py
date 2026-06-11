# 把 career_agent 的 state 进行分层存储
ALWAYS_KEEP_FIELDS = {
    "workflow_id",
    "workflow_status",
    "current_node",
    "checkpoint_version",
    "user_id",
    "session_id",
}

RECOVERY_KEEP_FIELDS = {
    "job_description",
    "resume_text",

    "jd_analysis",
    "execution_plan",
    "query_plan",

    "skill_evidence",
    "background_evidence",
    "rag_evidence",

    "react_decision",
    "retry_count",
    "max_retry",

    "resume_profile",
    "match_result",

    "learning_plan",
    "interview_tips",
    "cover_letter",

    "final_report",

    "application_history",
    "profile_summary",
    "preference",

    "available_tools",
}

CONFIRMATION_ONLY_FIELDS = {
    "confirmation_id",
    "human_action",
    "confirmation_status",
    "confirmation_message",
}

RUNTIME_ONLY_FIELDS = {
    "_current_step_id",
    "_current_token_usage",
}

UNCERTAIN_FIELDS = {
    "memories",
    "retry_evidence",
    "retry_added_count",
    "reflection_result",
}


CHECKPOINT_POLICIES = {
    "recovery": (
        ALWAYS_KEEP_FIELDS
        | RECOVERY_KEEP_FIELDS
        | CONFIRMATION_ONLY_FIELDS
    ),
    "confirmation": {
        "workflow_id",
        "workflow_status",
        "current_node",
        "user_id",
        "session_id",
        "job_description",
        "resume_text",
        "final_report",
        "confirmation_id",
        "confirmation_status",
        "confirmation_message",
        "retry_count",
        "max_retry",
        "retry_added_count",
        "confirmation_id",
        "human_action",
        "confirmation_status",
        "confirmation_message",
        "execution_plan",
        "query_plan",
        "react_decision",
        "available_tools",
    },
}

DROP_AFTER_NODE = {
    "job_description": "build_retrieval_queries",
    "resume_text": "extract_resume_profile",
    "query_plan": "extract_resume_profile",
    "execution_plan": "extract_resume_profile",
    "rag_evidence": "extract_resume_profile",
    "skill_evidence": "extract_resume_profile",
    "background_evidence": "extract_resume_profile",
    "react_decision": "extract_resume_profile",
}

CHECKPOINT_NODE_ORDER = [
    "build_retrieval_queries",
    "retrieve_resume_evidence",
    "extract_resume_profile",
    "generate_cover_letter",
    "create_confirmation",
]

def should_drop_by_lifecycle(key: str, current_node: str) -> bool:
    if current_node is None:
        return False
    if current_node not in CHECKPOINT_NODE_ORDER:
        return False

    drop_after_node = DROP_AFTER_NODE.get(key)
    if drop_after_node is None:
        return False
    if drop_after_node not in CHECKPOINT_NODE_ORDER:
        return False

    node_index = CHECKPOINT_NODE_ORDER.index(current_node)
    drop_index = CHECKPOINT_NODE_ORDER.index(drop_after_node)

    return node_index > drop_index

def build_checkpoint_state(state: dict, current_node: str, mode: str = "recovery") -> dict:
    checkpoint_keys = CHECKPOINT_POLICIES.get(mode)

    if checkpoint_keys is None:
        raise ValueError(f"Unsupported checkpoint mode: {mode}")

    return {
        key: state.get(key)
        for key in checkpoint_keys
        if key in state
        and key not in RUNTIME_ONLY_FIELDS
        and not should_drop_by_lifecycle(key, current_node)
    }