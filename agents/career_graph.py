import os
from typing import TypedDict, Any

import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from pydantic import ValidationError

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
from services.memory_service import MemoryService

from tools.rag_evidence_tool import retrieve_evidence_from_rag

memory_service = MemoryService()

load_dotenv()


# ============================================================
# 1. 定义 Agent 的 State
# ============================================================
class CareerAgentState(TypedDict):
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

    reflection_result: dict[str, Any]
    retry_evidence: list[dict[str, Any]]
    retry_count: int
    max_retry: int
    retry_added_count: int


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

        evidence_list = retrieve_evidence_from_rag(
            user_id=state["user_id"], query=final_query
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
    }


def reflect_evidence(state: CareerAgentState):
    prompt = REFLECT_EVIDENCE_PROMPT.format(
        query_plan=json.dumps(
            state.get("query_plan", {}), ensure_ascii=False, indent=2
        ),
        skill_evidence=json.dumps(
            state.get("skill_evidence", []), ensure_ascii=False, indent=2
        ),
    )

    response = json_llm.invoke(prompt)

    try:
        raw_dict = json.loads(response.content)
        reflection_result = ReflectionResult.model_validate(raw_dict).model_dump()
    except (json.JSONDecodeError, ValidationError) as e:
        print("\n====== reflect_evidence: 解析失败 ======")
        print(e)
        print(response.content)

        reflection_result = {"need_retry": False, "retry_queries": []}

    print("\n====== reflect_evidence: 输出 reflection_result ======")
    print(reflection_result)

    return {"reflection_result": reflection_result}


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

        evidence_list = retrieve_evidence_from_rag(
            user_id=state["user_id"], query=final_query
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
    }


def filter_matched_skills_without_evidence(match_result: dict):
    match_result["matched_skills"] = [
        item for item in match_result.get("matched_skills", []) if item.get("evidence")
    ]
    return match_result


# 废弃，deepseek 不支持 Pydantic 对象
# structured_jd_llm = llm.with_structured_output(JDAnalysis)


def build_retrieval_queries(state: CareerAgentState):

    prompt = BUILD_RETRIEVAL_QUERIES_PROMPT.format(
        jd_analysis=json.dumps(state["jd_analysis"], ensure_ascii=False, indent=2)
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

    return {"query_plan": query_plan}


def load_memory(state: CareerAgentState):
    session_id = state["session_id"]

    memories = memory_service.get_memories(session_id)

    print("\n====== load_memory: 历史 memories ======")
    print(memories)

    return {"memories": memories}


def save_memory(state: CareerAgentState):
    print("\n====== save_memory: 保存本次分析结果 ======")

    match = state["match_result"]

    memory = {
        "job_title": state["jd_analysis"].get("role_title", ""),
        "match_score": match.get("match_score", 0),
        "missing_skills": match.get("missing_skills", []),
        "summary": match.get("summary", ""),
    }

    memory_service.save_memory(session_id=state["session_id"], memory=memory)

    print(memory)

    return {}


def analyze_jd(state: CareerAgentState):
    prompt = ANALYZE_JD_PROMPT.format(job_description=state["job_description"])

    response = json_llm.invoke(prompt)

    try:
        # jd_analysis = json.loads(response.content)
        raw_dict = json.loads(response.content)
        jd_analysis = JDAnalysis.model_validate(raw_dict)
    except (json.JSONDecodeError, ValidationError) as e:
        print("\n====== analyze_jd: 解析失败 ======")
        print(e)
        print(response.content)
        jd_analysis = JDAnalysis(
            role_title="",
            required_skills=[],
            preferred_skills=[],
            frontend_skills=[],
            backend_skills=[],
            ai_skills=[],
            infra_skills=[],
            soft_skills=[],
            responsibilities=[],
        )
    # response = structured_jd_llm.invoke(prompt)
    print("\n====== analyze_jd: 输出 jd_analysis ======")
    print(jd_analysis)

    return {"jd_analysis": jd_analysis.model_dump()}


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

    return {"resume_profile": resume_profile.model_dump()}


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

    return {"match_result": match_result}


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
    return {"learning_plan": ""}


def generate_interview_tips(state: CareerAgentState):

    prompt = GENERATE_INTERVIEW_TIPS_PROMPT.format(
        jd_analysis=json.dumps(state["jd_analysis"], ensure_ascii=False),
        resume_profile=json.dumps(state["resume_profile"], ensure_ascii=False),
        match_result=json.dumps(state["match_result"], ensure_ascii=False),
        memories=json.dumps(state["memories"], ensure_ascii=False),
    )

    response = text_llm.invoke(prompt)

    return {"interview_tips": response.content}


# 路由函数
def route_by_score(state: CareerAgentState):

    score = state["match_result"]["match_score"]

    print(f"\n====== 当前 match_score: {score} ======")

    if score >= 80:
        return "generate_interview_tips"

    return "generate_learning_plan"


def route_after_reflection(state: CareerAgentState):
    reflection = state.get("reflection_result", {})

    if reflection.get("need_retry"):
        return "retry_retrieve_evidence"

    return "extract_resume_profile"


def generate_cover_letter(state: CareerAgentState):
    prompt = GENERATE_COVER_LETTER_PROMPT.format(
        jd_analysis=json.dumps(state["jd_analysis"], ensure_ascii=False),
        resume_profile=json.dumps(state["resume_profile"], ensure_ascii=False),
        match_result=json.dumps(state["match_result"], ensure_ascii=False),
    )

    response = text_llm.invoke(prompt)

    return {"cover_letter": response.content}


# ============================================================
# 4. Node 2：生成最终报告
# ============================================================
# 这个 node 不再调用 LLM。
# 它只是把上一步得到的 jd_analysis 包装成报告。
#
# 它读取：
#   state["jd_analysis"]
#
# 然后生成：
#   final_report
#
# 最后返回：
#   {"final_report": final_report}
# ============================================================
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

    return {"final_report": report}


# ============================================================
# 5. 构建 LangGraph 工作流
# ============================================================
# 这里是真正的 graph 定义部分。
#
# StateGraph(CareerAgentState)
# 表示：
#   这个图运行时使用 CareerAgentState 作为共享状态。
# add_node：
#   注册节点。
# add_edge：
#   定义节点之间的执行顺序。
# ============================================================
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
    graph.add_node("build_retrieval_queries", build_retrieval_queries)
    graph.add_node("retrieve_resume_evidence", retrieve_resume_evidence)

    graph.add_node("reflect_evidence", reflect_evidence)
    graph.add_node("retry_retrieve_evidence", retry_retrieve_evidence)

    graph.add_edge(START, "load_memory")
    graph.add_edge("load_memory", "analyze_jd")
    graph.add_edge("analyze_jd", "build_retrieval_queries")
    graph.add_edge("build_retrieval_queries", "retrieve_resume_evidence")

    graph.add_edge("retrieve_resume_evidence", "reflect_evidence")
    graph.add_conditional_edges("reflect_evidence", route_after_reflection)
    graph.add_edge("retry_retrieve_evidence", "extract_resume_profile")

    graph.add_edge("extract_resume_profile", "match_job")
    graph.add_conditional_edges("match_job", route_by_score)
    graph.add_edge("generate_learning_plan", "generate_cover_letter")
    graph.add_edge("generate_interview_tips", "generate_cover_letter")
    graph.add_edge("generate_cover_letter", "generate_report")
    graph.add_edge("generate_report", "save_memory")
    graph.add_edge("save_memory", END)

    return graph.compile()


career_graph = build_career_graph()


# ============================================================
# 7. 对外暴露一个简单函数
# ============================================================
# main.py 不需要知道 LangGraph 的细节。
#
# main.py 只需要调用：
#   run_career_agent(job_description)
#
# 这个函数内部会：
#   1. 初始化 state
#   2. 执行 graph
#   3. 返回 final_report
# ============================================================
def run_career_agent(
    session_id: str, user_id: str, job_description: str, resume_text: str
):
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
            "reflection_result": {},
            "retry_evidence": [],
            "retry_count": 0,
            "max_retry": 1,
            "retry_added_count": 0,
        }
    )

    return result["final_report"]
