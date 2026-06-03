import logging

from tools.career_tools import register_career_tools
from tools.tool_registry import tool_registry

logger = logging.getLogger(__name__)

def register_all_tools():
    register_career_tools()

    logger.info("\n====== Registered Tools ======")
    for tool in tool_registry.list_tools():
        logger.info(tool.name)
