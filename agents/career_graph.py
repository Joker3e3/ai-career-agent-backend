import os
from typing import TypedDict, Any

import json
import uuid
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from pydantic import ValidationError

from agents.career.trace import trace_node, trace_tool
from prompts.career_prompts import (
    ANALYZE_JD_PROMPT,
    EXTRACT_RESUME_PROMPT,
    MATCH_JOB_PROMPT,
    GENERATE_LEARNING_PLAN_PROMPT,
    GENERATE_INTERVIEW_TIPS_PROMPT,
    GENERATE_COVER_LETTER_PROMPT,
    BUILD_RETRIEVAL_QUERIES_PROMPT,
    REFLECT_EVIDENCE_PROMPT,
)
from schemas.jd_schema import JDAnalysis
from schemas.resume_schema import ResumeProfile
from schemas.match_schema import MatchResult
from schemas.query_schema import QueryPlan
from schemas.reflection_schema import ReflectionResult
from schemas.react_decision import ReactDecision
from services.session_memory_service import SessionMemoryService
from services.workflow_state_service import WorkflowStateService
from services.confirmation_service import ConfirmationService

from tools.rag_evidence_tool import retrieve_evidence_from_rag
from tools.tool_executor import call_tool
from tools.tool_registry import tool_registry

from database.repositories.agent_run_repository import (
    create_agent_run,
    get_agent_run_by_workflow_id,
    update_agent_run,
)
from database.repositories.human_confirmation_repository import (
    create_human_confirmation,
    update_human_confirmation,
)
from database.database import SessionLocal

from constants.workflow_status import ConfirmationStatus, WorkflowStatus
from utils.time import now_utc8

from agents.career.state_policy import build_checkpoint_state

session_memory_service = SessionMemoryService()
workflow_state_service = WorkflowStateService()
confirmation_service = ConfirmationService()


# ============================================================
class CareerAgentState(TypedDict, total=False):
    user_id: str
    session_id: str
    job_description: str
    resume_text: str
    jd_analysis: dict[str, Any]
    resume_profile: dict[str, Any]
    match_result: dict[str, Any]
    learning_plan: str
    interview_tips: str
    cover_letter: str
    memories: list[dict[str, Any]]
    final_report: str
    skill_evidence: list[dict]
    background_evidence: list[dict]
    rag_evidence: list[dict[str, Any]]
    query_plan: dict[str, Any]
    execution_plan: dict[str, Any]

    react_decision: dict[str, Any]
    retry_evidence: list[dict[str, Any]]
    retry_count: int
    max_retry: int
    retry_added_count: int

    workflow_id: str
    workflow_status: str
    current_node: str
    confirmation_id: str
    human_action: str
    confirmation_status: str
    confirmation_message: str
    available_tools: list[dict[str, Any]]


json_llm = ChatOpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_BASE_URL"),
    model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
    temperature=0.2,
    model_kwargs={"response_format": {"type": "json_object"}},
)

text_llm = ChatOpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_BASE_URL"),
    model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
    temperature=0.2,
)


@trace_node("retrieve_resume_evidence")
def retrieve_resume_evidence(state: CareerAgentState):

    all_evidence = []
    skill_evidence = []
    background_evidence = []
    seen_skill = set()
    seen_background = set()
    queries = state.get("query_plan", {}).get("queries", [])

    for item in queries:
        dimension = item.get("dimension", "")
        semantic_query = item.get("query", "")
        keywords = item.get("keywords", [])

        keyword_query = " ".join(keywords)

        final_query = f"{semantic_query}\n关键词：{keyword_query}"

        # evidence_list = retrieve_evidence_from_rag(
        #     user_id=state["user_id"],
        #     query=final_query,
        #     workflow_id=state["workflow_id"],
        #     step_id=state.get("_current_step_id"),
        # )
        evidence_list = call_tool(
            tool_name="resume_rag_retriever",
            user_id=state["user_id"],
            query=final_query,
            workflow_id=state["workflow_id"],
            step_id=state.get("_current_step_id"),
        )

        for evidence in evidence_list:
            content = evidence.get("content", "")

            if dimension == "background":
                if content in seen_background:
                    continue
                seen_background.add(content)
                all_evidence.append(evidence)
                background_evidence.append(evidence)
            else:
                if content in seen_skill:
                    continue
                seen_skill.add(content)
                all_evidence.append(evidence)
                skill_evidence.append(evidence)

    print("\n====== skill_evidence ======")
    print(skill_evidence)

    print("\n====== background_evidence ======")
    print(background_evidence)
    print("\n====== retrieve_resume_evidence: evidence ======")
    print(all_evidence)

    return {
        "rag_evidence": all_evidence,
        "skill_evidence": skill_evidence,
        "background_evidence": background_evidence,
        "current_node": "retrieve_resume_evidence",
    }


@trace_node("reflect_evidence")
def reflect_evidence(state: CareerAgentState):
    execution_plan = state.get("execution_plan", {})
    query_plan = state.get("query_plan", {})
    skill_evidence = state.get("skill_evidence", [])
    background_evidence = state.get("background_evidence", [])
    retry_count = state.get("retry_count", 0)
    max_retry = state.get("max_retry", 1)
    available_tools = state.get("available_tools", [])

    prompt = REFLECT_EVIDENCE_PROMPT.format(
        execution_plan=json.dumps(execution_plan, ensure_ascii=False, indent=2),
        query_plan=json.dumps(query_plan, ensure_ascii=False, indent=2),
        skill_evidence=json.dumps(skill_evidence, ensure_ascii=False, indent=2),
        background_evidence=json.dumps(
            background_evidence, ensure_ascii=False, indent=2
        ),
        available_tools=json.dumps(available_tools, ensure_ascii=False, indent=2),
        retry_count=retry_count,
        max_retry=max_retry,
    )

    response = json_llm.invoke(prompt)

    try:
        raw_dict = json.loads(response.content)
        react_decision = ReactDecision.model_validate(raw_dict).model_dump()
    except (json.JSONDecodeError, ValidationError) as e:
        print("\n====== reflect_evidence: 解析失败 ======")
        print(e)
        print(response.content)

        react_decision = {
            "decision": "continue",
            "thought": "反思结果解析失败，为避免无限循环，默认继续生成报告。",
            "tool_name": None,
            "tool_input": None,
        }

    print("\n====== reflect_evidence: 输出 react_decision ======")
    print(react_decision)

    return {
        "react_decision": react_decision,
        "current_node": "reflect_evidence",
    }


@trace_node("execute_react_action")
def execute_react_action(state: CareerAgentState):
    react_decision = state.get("react_decision", {})

    tool_name = react_decision.get("tool_name")
    tool_input = react_decision.get("tool_input") or {}

    if not tool_name:
        return {
            "current_node": "execute_react_action",
        }

    query = tool_input.get("query", "")
    keyword_query = tool_input.get("keywords", [""])
    final_query = f"{query}\n关键词：{keyword_query}"

    evidence_list = call_tool(
        tool_name=tool_name,
        user_id=state["user_id"],
        query=final_query,
        workflow_id=state["workflow_id"],
        step_id=state.get("_current_step_id"),
    )

    retry_count = state.get("retry_count", 0) + 1

    return {
        "retry_evidence": evidence_list,
        "retry_added_count": len(evidence_list),
        "rag_evidence": state.get("rag_evidence", []) + evidence_list,
        "skill_evidence": state.get("skill_evidence", []) + evidence_list,
        "retry_count": retry_count,
        "current_node": "execute_react_action",
    }


@trace_node("retry_retrieve_evidence")
def retry_retrieve_evidence(state: CareerAgentState):
    reflection = state.get("reflection_result", {})

    if not reflection.get("need_retry"):
        return {"retry_evidence": []}

    # 记录重试次数，避免死循环
    retry_count = state.get("retry_count", 0) + 1
    retry_evidence = []
    seen_contents = {item.get("content", "") for item in state.get("rag_evidence", [])}

    for item in reflection.get("retry_queries", []):
        dimension = item.get("dimension", "")
        retry_query = item.get("retry_query", "")
        keywords = item.get("keywords", [])

        final_query = f"{retry_query}\n关键词：{' '.join(keywords)}"

        # evidence_list = retrieve_evidence_from_rag(
        #     user_id=state["user_id"],
        #     query=final_query,
        #     workflow_id=state["workflow_id"],
        #     step_id=state.get("_current_step_id"),
        # )
        evidence_list = call_tool(
            tool_name="resume_rag_retriever",
            user_id=state["user_id"],
            query=final_query,
            workflow_id=state["workflow_id"],
            step_id=state.get("_current_step_id"),
        )

        for evidence in evidence_list:
            content = evidence.get("content", "")
            if not content or content in seen_contents:
                continue

            seen_contents.add(content)

            evidence["retrieval_dimension"] = dimension
            evidence["retrieval_query"] = final_query
            evidence["retrieval_type"] = "retry"

            retry_evidence.append(evidence)

    print("\n====== retry_retrieve_evidence: 输出 retry_evidence ======")
    print(retry_evidence)

    print(
        f"\n====== retry_retrieve_evidence: 重试次数 ====== {retry_count} ======  新增证据数 ====== {len(retry_evidence)} ======"
    )
    return {
        "retry_count": retry_count,
        "retry_added_count": len(retry_evidence),
        "retry_evidence": retry_evidence,
        "rag_evidence": state.get("rag_evidence", []) + retry_evidence,
        "skill_evidence": state.get("skill_evidence", []) + retry_evidence,
        "current_node": "retry_retrieve_evidence",
    }


@trace_node("create_confirmation")
def create_confirmation(state: CareerAgentState):
    confirmation_id = f"confirm_{uuid.uuid4()}"
    match_score = state.get("match_result", {}).get("match_score")
    confirmation_service.save_confirmation(
        confirmation_id=confirmation_id,
        data={
            "confirmation_id": confirmation_id,
            "workflow_id": state["workflow_id"],
            "status": "pending",
            "action_type": "cover_letter_approval",
            "user_action": "",
        },
    )

    updated_state = {
        **state,
        "confirmation_id": confirmation_id,
        "workflow_status": "waiting_human_confirmation",
        "current_node": "create_confirmation",
    }

    full_state_json = json.dumps(updated_state, ensure_ascii=False)
    checkpoint_state = build_checkpoint_state(updated_state)
    checkpoint_json = json.dumps(checkpoint_state, ensure_ascii=False)

    print("full_state size:", len(full_state_json))
    print("checkpoint_state size:", len(checkpoint_json))

    workflow_state_service.save_state(
        workflow_id=state["workflow_id"], state=checkpoint_state
    )

    db = SessionLocal()

    try:
        # create_agent_run(
        #     db=db,
        #     workflow_id=state["workflow_id"],
        #     user_id=state["user_id"],
        #     run_type="career_analysis",
        #     status=WorkflowStatus.WAITING_HUMAN_CONFIRMATION.value,
        #     input_summary=state["job_description"][:200],
        #     jd_text=state["job_description"],
        #     match_score=match_score,
        #     final_report=state["final_report"],
        #     started_at=now_utc8(),
        # )
        update_agent_run(
            db=db,
            workflow_id=state["workflow_id"],
            status=WorkflowStatus.WAITING_HUMAN_CONFIRMATION.value,
            match_score=match_score,
            final_report=state["final_report"],
        )

        create_human_confirmation(
            db=db,
            confirmation_id=confirmation_id,
            workflow_id=state["workflow_id"],
            actor_id=state["user_id"],
            action_type="cover_letter_approval",
            status=ConfirmationStatus.PENDING.value,
            payload_snapshot=state.get("cover_letter", ""),
        )

        db.commit()

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()

    print("create_confirmation")

    return {
        "confirmation_id": confirmation_id,
        "workflow_status": "waiting_human_confirmation",
        "current_node": "create_confirmation",
    }


def filter_matched_skills_without_evidence(match_result: dict):
    match_result["matched_skills"] = [
        item for item in match_result.get("matched_skills", []) if item.get("evidence")
    ]
    return match_result


# 废弃，deepseek 不支持 Pydantic 对象
# structured_jd_llm = llm.with_structured_output(JDAnalysis)


@trace_node("plan_career_analysis")
def plan_career_analysis(state: CareerAgentState):
    jd_analysis = state.get("jd_analysis", {})

    requirements = jd_analysis.get("requirements", [])

    retrieval_dimensions = []

    for item in requirements:
        retrieval_dimensions.append(
            {
                "dimension": item.get("dimension", ""),
                "priority": item.get("priority", "medium"),
                "keywords": item.get("keywords", []),
                "purpose": item.get("description", ""),
                "source": "jd_requirement",
            }
        )

    retrieval_dimensions.append(
        {
            "dimension": "background",
            "priority": "required",
            "keywords": [
                "教育经历",
                "学历",
                "工作经历",
                "项目经历",
                "个人背景",
                "求职优势",
            ],
            "purpose": "检索候选人的教育经历、整体经历、项目概述和求职优势，用于简历画像、求职自我介绍和 Cover Letter",
            "source": "system_required",
        }
    )

    execution_plan = {
        "goal": "评估候选人与岗位要求的匹配度，并生成求职分析报告、学习建议、面试建议和 Cover Letter",
        "role_title": jd_analysis.get("role_title", ""),
        "role_category": jd_analysis.get("role_category", "other"),
        "retrieval_policy": {
            "max_queries": 5,
            "must_include_background_query": True,
            "prioritize_high_priority_requirements": True,
        },
        "retrieval_dimensions": retrieval_dimensions,
        "retry_policy": {
            "max_retry": state.get("max_retry", 1),
            "retry_when": "关键能力维度缺少证据或检索结果不足以支撑匹配结论",
        },
        "output_requirements": {
            "final_report": True,
            "learning_plan": True,
            "interview_tips": True,
            "cover_letter": True,
        },
        "next_action": "build_retrieval_queries",
    }

    print("\n====== plan_career_analysis: 输出 execution_plan ======")
    print(execution_plan)

    return {
        "execution_plan": execution_plan,
        "current_node": "plan_career_analysis",
    }


@trace_node("build_retrieval_queries")
def build_retrieval_queries(state: CareerAgentState):
    execution_plan = state.get("execution_plan", {})

    prompt = BUILD_RETRIEVAL_QUERIES_PROMPT.format(
        execution_plan=execution_plan,
    )

    response = json_llm.invoke(prompt)

    try:
        raw_dict = json.loads(response.content)
        query_plan = QueryPlan.model_validate(raw_dict).model_dump()
    except (json.JSONDecodeError, ValidationError) as e:
        print("\n====== build_retrieval_queries: 解析失败 ======")
        print(e)
        print(response.content)

        query_plan = {"queries": []}

    print("\n====== build_retrieval_queries: 输出 query_plan ======")
    print(query_plan)

    return {"query_plan": query_plan, "current_node": "build_retrieval_queries"}


@trace_node("load_memory")
def load_memory(state: CareerAgentState):
    user_id = state["user_id"]
    session_id = state["session_id"]

    memories = session_memory_service.get_memories(
        user_id=user_id, session_id=session_id
    )

    print("\n====== load_memory: 历史 memories ======")
    print(memories)

    return {"memories": memories, "current_node": "load_memory"}


@trace_node("save_memory")
def save_memory(state: CareerAgentState):
    print("\n====== save_memory: 保存本次分析结果 ======")

    match = state["match_result"]

    memory = {
        "job_title": state["jd_analysis"].get("role_title", ""),
        "match_score": match.get("match_score", 0),
        "missing_skills": match.get("missing_skills", []),
        "summary": match.get("summary", ""),
    }

    session_memory_service.save_memory(
        user_id=state["user_id"], session_id=state["session_id"], memory=memory
    )

    print(memory)

    return {"current_node": "save_memory"}


@trace_node("analyze_jd")
def analyze_jd(state: CareerAgentState):
    prompt = ANALYZE_JD_PROMPT.format(job_description=state["job_description"])

    response = json_llm.invoke(prompt)

    try:
        raw_dict = json.loads(response.content)
        jd_analysis = JDAnalysis.model_validate(raw_dict)

    except (json.JSONDecodeError, ValidationError) as e:
        print("\n====== analyze_jd: 解析失败 ======")
        print(e)
        print(response.content)

        jd_analysis = JDAnalysis(
            role_title="",
            role_category="other",
            requirements=[],
            responsibilities=[],
            background_requirements=[],
        )

    print("\n====== analyze_jd: 输出 jd_analysis ======")
    print(jd_analysis)

    return {
        "jd_analysis": jd_analysis.model_dump(),
        "current_node": "analyze_jd",
    }


@trace_node("extract_resume_profile")
def extract_resume_profile(state: CareerAgentState):

    prompt = EXTRACT_RESUME_PROMPT.format(
        skill_evidence=json.dumps(
            state.get("skill_evidence", []), ensure_ascii=False, indent=2
        ),
        background_evidence=json.dumps(
            state.get("background_evidence", []), ensure_ascii=False, indent=2
        ),
        resume_text=state.get("resume_text", ""),
    )

    response = json_llm.invoke(prompt)

    try:
        raw_dict = json.loads(response.content)
        resume_profile = ResumeProfile.model_validate(raw_dict)
    except (json.JSONDecodeError, ValidationError) as e:
        print("\n====== extract_resume_profile: 解析失败 ======")
        print(e)
        print(response.content)

        resume_profile = ResumeProfile(
            frontend_skills=[],
            backend_skills=[],
            ai_skills=[],
            infra_skills=[],
            projects=[],
            education="",
            summary="",
        )

    print("\n====== extract_resume_profile: 输出 resume_profile ======")
    print(resume_profile)

    return {
        "resume_profile": resume_profile.model_dump(),
        "current_node": "extract_resume_profile",
    }


@trace_node("match_job")
def match_job(state: CareerAgentState):

    prompt = MATCH_JOB_PROMPT.format(
        jd_analysis=json.dumps(state["jd_analysis"], ensure_ascii=False),
        resume_profile=json.dumps(state["resume_profile"], ensure_ascii=False),
    )

    response = json_llm.invoke(prompt)

    try:
        raw_dict = json.loads(response.content)
        match_result = MatchResult.model_validate(raw_dict).model_dump()
        match_result = filter_matched_skills_without_evidence(match_result)
    except (json.JSONDecodeError, ValidationError) as e:
        print("\n====== match_job: 解析失败 ======")
        print(e)
        print(response.content)

        match_result = MatchResult(
            match_score=0,
            matched_skills=[],
            missing_skills=[],
            strengths=[],
            risks=[],
            summary="",
        )

    print("\n====== match_job: 输出 match_result ======")
    print(match_result)

    return {"match_result": match_result, "current_node": "match_job"}


@trace_node("generate_learning_plan")
def generate_learning_plan(state: CareerAgentState):

    print("\n====== generate_learning_plan: 输入 state ======")
    print(state)
    prompt = GENERATE_LEARNING_PLAN_PROMPT.format(
        jd_analysis=json.dumps(state["jd_analysis"], ensure_ascii=False),
        resume_profile=json.dumps(state["resume_profile"], ensure_ascii=False),
        match_result=json.dumps(state["match_result"], ensure_ascii=False),
        memories=json.dumps(state["memories"], ensure_ascii=False),
    )

    # response = text_llm.invoke(prompt)

    # print("\n====== generate_learning_plan: 输出 ======")
    # print(response)
    # return {"learning_plan": response.content}
    return {"learning_plan": "", "current_node": "generate_learning_plan"}


@trace_node("generate_interview_tips")
def generate_interview_tips(state: CareerAgentState):

    prompt = GENERATE_INTERVIEW_TIPS_PROMPT.format(
        jd_analysis=json.dumps(state["jd_analysis"], ensure_ascii=False),
        resume_profile=json.dumps(state["resume_profile"], ensure_ascii=False),
        match_result=json.dumps(state["match_result"], ensure_ascii=False),
        memories=json.dumps(state["memories"], ensure_ascii=False),
    )

    response = text_llm.invoke(prompt)

    return {
        "interview_tips": response.content,
        "current_node": "generate_interview_tips",
    }


# 路由函数
def route_by_score(state: CareerAgentState):

    score = state["match_result"]["match_score"]

    print(f"\n====== 当前 match_score: {score} ======")

    if score >= 80:
        return "generate_interview_tips"

    return "generate_learning_plan"


def route_after_reflection(state: CareerAgentState):
    react_decision = state.get("react_decision", {})
    retry_count = state.get("retry_count", 0)
    max_retry = state.get("max_retry", 1)

    if (
        react_decision.get("decision") == "act"
        and retry_count < max_retry
        and react_decision.get("tool_name")
    ):
        return "execute_react_action"

    return "extract_resume_profile"


@trace_node("generate_cover_letter")
def generate_cover_letter(state: CareerAgentState):
    prompt = GENERATE_COVER_LETTER_PROMPT.format(
        jd_analysis=json.dumps(state["jd_analysis"], ensure_ascii=False),
        resume_profile=json.dumps(state["resume_profile"], ensure_ascii=False),
        match_result=json.dumps(state["match_result"], ensure_ascii=False),
    )

    response = text_llm.invoke(prompt)

    return {"cover_letter": response.content, "current_node": "generate_cover_letter"}


# ============================================================
@trace_node("generate_report")
def generate_report(state: CareerAgentState):
    report = f"""
# AI 求职分析报告

## 一、岗位名称

{state["jd_analysis"].get("role_title", "")}

---

## 二、匹配评分

{state["match_result"].get("match_score", 0)}

---

## 三、已匹配技能

"""

    for skill in state["match_result"].get("matched_skills", []):

        report += f"""
- {skill["skill"]}
  - 证据：{skill["evidence"]}
"""

    report += "\n---\n"

    report += """
## 四、缺失技能

"""

    for skill in state["match_result"].get("missing_skills", []):

        report += f"- {skill}\n"

    report += "\n---\n"

    report += """
## 五、优势分析

"""

    for item in state["match_result"].get("strengths", []):

        report += f"- {item}\n"

    report += "\n---\n"

    report += """
## 六、风险分析

"""

    for item in state["match_result"].get("risks", []):

        report += f"- {item}\n"

    report += "\n---\n"

    if state.get("learning_plan"):

        report += f"""
## 七、学习路线建议

{state["learning_plan"]}

---
"""

    if state.get("interview_tips"):

        report += f"""
## 八、面试准备建议

{state["interview_tips"]}

---
"""

    report += f"""
## 九、投递邮件草稿

{state["cover_letter"]}
"""

    return {"final_report": report, "current_node": "generate_report"}


@trace_node("confirm_node")
def confirm_node(state: CareerAgentState):

    action = state.get("human_action", "")

    if action == "approve":
        confirmation_status = "approved"
        confirmation_message = "用户已确认使用该投递草稿。当前版本不执行真实投递。"
    elif action == "revise":
        confirmation_status = "revise_required"
        confirmation_message = "用户要求修改投递草稿。"
    elif action == "reject":
        confirmation_status = "rejected"
        confirmation_message = "用户暂不使用该投递草稿。"
    else:
        confirmation_status = "invalid"
        confirmation_message = "未知确认动作。"

    print(
        f"\n====== confirm_node: 输出 confirmation_status ======{confirmation_status} =========== confirmation_message:{confirmation_message}"
    )
    return {
        "human_action": action,
        "confirmation_status": confirmation_status,
        "confirmation_message": confirmation_message,
        "workflow_status": "completed",
        "current_node": "confirm_node",
    }


# ===========================================================
def build_career_graph():
    graph = StateGraph(CareerAgentState)

    graph.add_node("load_memory", load_memory)
    graph.add_node("save_memory", save_memory)
    graph.add_node("analyze_jd", analyze_jd)
    graph.add_node("extract_resume_profile", extract_resume_profile)
    graph.add_node("match_job", match_job)
    graph.add_node("generate_report", generate_report)

    graph.add_node("generate_learning_plan", generate_learning_plan)
    graph.add_node("generate_interview_tips", generate_interview_tips)
    graph.add_node("generate_cover_letter", generate_cover_letter)
    graph.add_node("plan_career_analysis", plan_career_analysis)
    graph.add_node("build_retrieval_queries", build_retrieval_queries)
    graph.add_node("retrieve_resume_evidence", retrieve_resume_evidence)

    graph.add_node("reflect_evidence", reflect_evidence)
    graph.add_node("execute_react_action", execute_react_action)
    graph.add_node("retry_retrieve_evidence", retry_retrieve_evidence)
    graph.add_node("create_confirmation", create_confirmation)

    graph.add_edge(START, "load_memory")
    graph.add_edge("load_memory", "analyze_jd")
    graph.add_edge("analyze_jd", "plan_career_analysis")
    graph.add_edge("plan_career_analysis", "build_retrieval_queries")
    graph.add_edge("build_retrieval_queries", "retrieve_resume_evidence")

    graph.add_edge("retrieve_resume_evidence", "reflect_evidence")
    graph.add_conditional_edges("reflect_evidence", route_after_reflection)
    graph.add_edge("execute_react_action", "reflect_evidence")

    graph.add_edge("extract_resume_profile", "match_job")
    graph.add_conditional_edges("match_job", route_by_score)
    graph.add_edge("generate_learning_plan", "generate_cover_letter")
    graph.add_edge("generate_interview_tips", "generate_cover_letter")
    graph.add_edge("generate_cover_letter", "generate_report")
    graph.add_edge("generate_report", "save_memory")
    graph.add_edge("save_memory", "create_confirmation")
    graph.add_edge("create_confirmation", END)

    return graph.compile()


career_graph = build_career_graph()


def build_confirm_graph():
    confirm_graph = StateGraph(CareerAgentState)

    confirm_graph.add_node("confirm_node", confirm_node)

    confirm_graph.add_edge(START, "confirm_node")
    confirm_graph.add_edge("confirm_node", END)

    return confirm_graph.compile()


confirm_graph = build_confirm_graph()


# ============================================================
# 7. 对外暴露一个简单函数
# ============================================================
def run_career_agent(
    session_id: str, user_id: str, job_description: str, resume_text: str
):
    available_tools = tool_registry.get_tool_summaries()
    print(f"\n=====available_tools======{available_tools}")
    result = career_graph.invoke(
        {
            "user_id": user_id,
            "session_id": session_id,
            "job_description": job_description,
            "resume_text": resume_text,
            "jd_analysis": {},
            "resume_profile": {},
            "match_result": {},
            "learning_plan": "",
            "interview_tips": "",
            "cover_letter": "",
            "memories": [],
            "final_report": "",
            "rag_evidence": [],
            "skill_evidence": [],
            "background_evidence": [],
            "query_plan": {},
            "execution_plan": {},
            "react_decision": {},
            "retry_evidence": [],
            "retry_count": 0,
            "max_retry": 1,
            "retry_added_count": 0,
            "workflow_id": f"workflow_{uuid.uuid4()}",
            "workflow_status": "running",
            "current_node": "",
            "confirmation_id": "",
            "human_action": "",
            "confirmation_status": "",
            "confirmation_message": "",
            "available_tools": available_tools,
        }
    )

    return {
        "workflow_id": result["workflow_id"],
        "confirmation_id": result["confirmation_id"],
        "workflow_status": result["workflow_status"],
        "report": result["final_report"],
    }


def run_confirm_workflow(workflow_id: str, confirmation_id: str, human_action: str):
    saved_state = workflow_state_service.get_state(workflow_id)

    if not saved_state:
        return {"success": False, "message": "workflow 不存在"}

    confirmation = confirmation_service.get_confirmation(confirmation_id)

    if not confirmation:
        return {"success": False, "message": "confirmation 不存在或已过期"}

    if confirmation.get("workflow_id") != workflow_id:
        return {"success": False, "message": "confirmation 不属于该 workflow"}

    if confirmation.get("status") != "pending":
        return {
            "success": False,
            "message": "该 confirmation 已处理，不能重复确认",
            "confirmation_status": confirmation.get("status"),
        }

    saved_state["human_action"] = human_action

    result = confirm_graph.invoke(saved_state)

    # 修改Redis内存
    confirmation_service.update_confirmation(
        confirmation_id=confirmation_id,
        updates={
            "status": result["confirmation_status"],
            "user_action": human_action,
            "workflow_status": result["workflow_status"],
            "message": result.get("confirmation_message", ""),
        },
    )

    workflow_state_service.update_state(workflow_id=workflow_id, updates=result)

    # 改PostSQL
    db = SessionLocal()
    try:
        update_human_confirmation(
            db=db,
            confirmation_id=confirmation_id,
            status=result["confirmation_status"],
            user_action=human_action,
            message=result.get("confirmation_message"),
        )

        update_agent_run(
            db=db,
            workflow_id=workflow_id,
            status=WorkflowStatus.COMPLETED.value,
            completed_at=now_utc8(),
        )

        db.commit()

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()

    return {
        "success": True,
        "workflow_id": workflow_id,
        "confirmation_id": confirmation_id,
        "confirmation_status": result["confirmation_status"],
        "confirmation_message": result.get("confirmation_message", ""),
        "workflow_status": result["workflow_status"],
    }
