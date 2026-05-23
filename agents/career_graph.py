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
)
from schemas.jd_schema import JDAnalysis
from schemas.resume_schema import ResumeProfile
from schemas.match_schema import MatchResult
from services.memory_service import MemoryService

memory_service = MemoryService()

load_dotenv()


# ============================================================
# 1. 定义 Agent 的 State
# ============================================================
class CareerAgentState(TypedDict):
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


# 废弃，deepseek 不支持 Pydantic 对象
# structured_jd_llm = llm.with_structured_output(JDAnalysis)


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

    prompt = EXTRACT_RESUME_PROMPT.format(resume_text=state["resume_text"])

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
        match_result = MatchResult.model_validate(raw_dict)
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

    return {"match_result": match_result.model_dump()}


def generate_learning_plan(state: CareerAgentState):

    print("\n====== generate_learning_plan: 输入 state ======")
    print(state)
    prompt = GENERATE_LEARNING_PLAN_PROMPT.format(
        jd_analysis=json.dumps(state["jd_analysis"], ensure_ascii=False),
        resume_profile=json.dumps(state["resume_profile"], ensure_ascii=False),
        match_result=json.dumps(state["match_result"], ensure_ascii=False),
        memories=json.dumps(state["memories"], ensure_ascii=False),
    )

    response = text_llm.invoke(prompt)

    print("\n====== generate_learning_plan: 输出 ======")
    print(response)
    return {"learning_plan": response.content}


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

    for skill in state["match_result"].get(
        "matched_skills",
        []
    ):

        report += f"""
- {skill["skill"]}
  - 证据：{skill["evidence"]}
"""

    report += "\n---\n"

    report += """
## 四、缺失技能

"""

    for skill in state["match_result"].get(
        "missing_skills",
        []
    ):

        report += f"- {skill}\n"

    report += "\n---\n"

    report += """
## 五、优势分析

"""

    for item in state["match_result"].get(
        "strengths",
        []
    ):

        report += f"- {item}\n"

    report += "\n---\n"

    report += """
## 六、风险分析

"""

    for item in state["match_result"].get(
        "risks",
        []
    ):

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

    return {
        "final_report": report
    }


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

    graph.add_edge(START, "load_memory")
    graph.add_edge("load_memory", "analyze_jd")
    graph.add_edge("analyze_jd", "extract_resume_profile")
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
def run_career_agent(session_id: str, job_description: str, resume_text: str):
    result = career_graph.invoke(
        {
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
        }
    )

    return result["final_report"]
