# 把 career_agent 的 state 进行分层存储
CHECKPOINT_FIELDS = {
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
}

CONTROL_FIELDS = {
    "execution_plan",
    "query_plan",
    "react_decision",
    "available_tools",
}

EPHEMERAL_FIELDS = {
    "jd_analysis",
    "rag_evidence",
    "skill_evidence",
    "background_evidence",
    "reflection_result",
    "retry_evidence",
    "resume_profile",
    "match_result",
    "learning_plan",
    "interview_tips",
    "cover_letter",
}

RUNTIME_COUNTER_FIELDS = {
    "retry_count",
    "max_retry",
    "retry_added_count",
}

MEMORY_FIELDS = {
    "memories",
    "application_history",
    "profile_summary",
    "preference",
}

CONFIRMATION_FIELDS = {
    "confirmation_id",
    "human_action",
    "confirmation_status",
    "confirmation_message",
}

def build_checkpoint_state(state: dict) -> dict:
    checkpoint_keys = (
        CHECKPOINT_FIELDS
        | RUNTIME_COUNTER_FIELDS
        | CONFIRMATION_FIELDS
        | CONTROL_FIELDS
    )

    return {
        key: state.get(key)
        for key in checkpoint_keys
        if key in state
    }