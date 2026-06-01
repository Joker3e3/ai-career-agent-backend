from tools.tool_registry import ToolDefinition, tool_registry
from tools.rag_evidence_tool import retrieve_evidence_from_rag


def register_career_tools():
    tool_registry.register(
        ToolDefinition(
            name="resume_rag_retriever",
            tool_type="rag",
            description="从候选人简历 RAG 知识库中检索与岗位能力维度相关的证据",
            func=retrieve_evidence_from_rag,
        )
    )

