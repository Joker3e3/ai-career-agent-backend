import asyncio
import logging

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from agents.career.trace import trace_tool

logger = logging.getLogger(__name__)

@trace_tool(
    tool_name="resume_rag_retriever",
    tool_type="rag",
)
def retrieve_evidence_from_mcp_rag(
    user_id: str,
    query: str,
    candidate_id: str,
    resume_id: str,
    workflow_id: str | None = None,
    step_id: int | None = None,
) -> list[dict]:
    logger.info("====== Calling RAG through MCP ======")
    return asyncio.run(
        call_mcp_resume_rag_retriever(
            user_id=user_id,
            query=query,
            candidate_id=candidate_id,
            resume_id=resume_id,
        )
    )


async def call_mcp_resume_rag_retriever(
    user_id: str,
    query: str,
    candidate_id: str,
    resume_id: str,
) -> list[dict]:
    # 告诉 MCP Client：
    # 如何启动 MCP Server
    # 等价于命令：
    #
    # uv run python mcp_server.py
    #
    server_params = StdioServerParameters(
        command="uv",
        args=[
            "run",
            "python",
            "mcp_server.py",
        ],
    )

    # 启动 MCP Server 子进程
    #
    # 并建立 stdio 通信管道：
    #
    # MCP Client
    #     ↕ stdin/stdout
    # MCP Server
    #
    async with stdio_client(server_params) as (read_stream, write_stream):
        # 创建 MCP Session
        async with ClientSession(read_stream, write_stream) as session:
            # MCP Client 与 MCP Server 握手
            await session.initialize()

            # 调用 MCP Tool
            result = await session.call_tool(
                "resume_rag_retriever",
                arguments={
                    "user_id": user_id,
                    "query": query,
                    "candidate_id": candidate_id,
                    "resume_id": resume_id,
                },
            )

            if getattr(result, "structuredContent", None):
                structured = result.structuredContent

                if isinstance(structured, dict) and "result" in structured:
                    return structured["result"]

                if isinstance(structured, list):
                    return structured

                return [structured]

            if getattr(result, "content", None):
                text = result.content[0].text
                return [{"content": text, "metadata": {}}]

            return []
