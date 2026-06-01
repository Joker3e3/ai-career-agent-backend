import json

from database.repositories.user_memories_repository import (
    create_user_memory,
    upsert_user_memory,
    list_user_memories,
)
from prompts.career_prompts import (
    UPDATE_PREFERENCE_PROMPT,
    UPDATE_PROFILE_SUMMARY_PROMPT,
)
from llms.llm_client import text_llm, json_llm


def load_long_term_memories(
    user_id: str,
    limit: int = 5,
):
    application_histories = list_user_memories(
        user_id=user_id,
        memory_type="application_history",
        limit=limit,
    )

    profile_summaries = list_user_memories(
        user_id=user_id,
        memory_type="profile_summary",
        limit=1,
    )

    preferences = list_user_memories(
        user_id=user_id,
        memory_type="preference",
        limit=1,
    )

    return {
        "application_history": [memory.content for memory in application_histories],
        "profile_summary": (profile_summaries[0].content if profile_summaries else ""),
        "preference": (preferences[0].content if preferences else ""),
    }


def save_application_history(
    user_id: str,
    workflow_id: str,
    jd_analysis: dict,
    match_result: dict,
    final_report: str,
):
    content = {
        "jd_analysis": jd_analysis,
        "match_result": match_result,
        "final_report": final_report,
    }

    return create_user_memory(
        user_id=user_id,
        memory_type="application_history",
        content=json.dumps(content, ensure_ascii=False),
        source_workflow_id=workflow_id,
    )


def update_user_long_term_memory(
    user_id: str,
    jd_analysis: dict,
    match_result: dict,
    final_report: str,
):
    old_memories = load_long_term_memories(user_id=user_id)

    old_profile_summary = old_memories.get(
        "profile_summary",
        "",
    )

    old_preference = old_memories.get(
        "preference",
        "",
    )

    updated_profile_summary = generate_updated_profile_summary(
        old_profile_summary=old_profile_summary,
        jd_analysis=jd_analysis,
        match_result=match_result,
        final_report=final_report,
    )

    updated_preference = generate_updated_preference(
        old_preference=old_preference,
        jd_analysis=jd_analysis,
        match_result=match_result,
    )

    upsert_user_memory(
        user_id=user_id,
        memory_type="profile_summary",
        content=updated_profile_summary,
        source_workflow_id=None,
    )

    upsert_user_memory(
        user_id=user_id,
        memory_type="preference",
        content=updated_preference,
        source_workflow_id=None,
    )

    return {
        "profile_summary": updated_profile_summary,
        "preference": updated_preference,
    }


def generate_updated_profile_summary(
    old_profile_summary: str,
    jd_analysis: dict,
    match_result: dict,
    final_report: str,
):
    prompt = UPDATE_PROFILE_SUMMARY_PROMPT.format(
        old_profile_summary=old_profile_summary or "暂无",
        jd_analysis=json.dumps(
            jd_analysis,
            ensure_ascii=False,
            indent=2,
        ),
        match_result=json.dumps(
            match_result,
            ensure_ascii=False,
            indent=2,
        ),
        final_report=final_report[:1500],
    )

    response = text_llm.invoke(prompt)

    return response.content.strip()


def generate_updated_preference(
    old_preference: str,
    jd_analysis: dict,
    match_result: dict,
):
    prompt = UPDATE_PREFERENCE_PROMPT.format(
        old_preference=old_preference or "暂无",
        jd_analysis=json.dumps(
            jd_analysis,
            ensure_ascii=False,
            indent=2,
        ),
        match_result=json.dumps(
            match_result,
            ensure_ascii=False,
            indent=2,
        ),
    )

    response = text_llm.invoke(prompt)

    return response.content.strip()
