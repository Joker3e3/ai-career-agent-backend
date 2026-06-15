import logging

from mcp.server.fastmcp import FastMCP

from tools.rag_evidence_tool import mcp_retrieve_evidence_from_rag

mcp = FastMCP("ai-career-agent-tools")

logger = logging.getLogger(__name__)
@mcp.tool()
def resume_rag_retriever(
    user_id: str,
    query: str,
    candidate_id: str,
    resume_id: str
) -> list[dict]:
    """
    从候选人简历 RAG 知识库中检索与岗位能力维度相关的证据。
    """

    logger.info("====== MCP Server tool called: resume_rag_retriever ======")
    return mcp_retrieve_evidence_from_rag(
        user_id=user_id,
        query=query,
        candidate_id=candidate_id,
        resume_id=resume_id
    )


if __name__ == "__main__":
    mcp.run()
