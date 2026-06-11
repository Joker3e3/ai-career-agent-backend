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
    "confirmation": (
        ALWAYS_KEEP_FIELDS
        | RECOVERY_KEEP_FIELDS
        | CONFIRMATION_ONLY_FIELDS
    ),
}


def build_checkpoint_state(state: dict, mode: str = "recovery") -> dict:
    checkpoint_keys = CHECKPOINT_POLICIES.get(mode)

    if checkpoint_keys is None:
        raise ValueError(f"Unsupported checkpoint mode: {mode}")

    return {
        key: state.get(key)
        for key in checkpoint_keys
        if key in state
    }