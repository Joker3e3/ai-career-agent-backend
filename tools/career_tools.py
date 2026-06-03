import logging

from tools.mcp_tools import retrieve_evidence_from_mcp_rag
from tools.tool_registry import ToolDefinition, tool_registry
from tools.rag_evidence_tool import retrieve_evidence_from_rag
from config.settings import USE_MCP_TOOLS

logger = logging.getLogger(__name__)


def register_career_tools():
    rag_tool_func = (
        retrieve_evidence_from_mcp_rag if USE_MCP_TOOLS else retrieve_evidence_from_rag
    )
    logger.info(f"USE_MCP_TOOLS={USE_MCP_TOOLS}")
    logger.info(f"Register resume_rag_retriever func={rag_tool_func.__name__}")
    tool_registry.register(
        ToolDefinition(
            name="resume_rag_retriever",
            tool_type="rag",
            description="从候选人简历 RAG 知识库中检索与岗位能力维度相关的证据",
            func=rag_tool_func,
        )
    )
