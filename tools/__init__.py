from tools.career_tools import register_career_tools
from tools.tool_registry import tool_registry


def register_all_tools():
    register_career_tools()

    print("\n====== Registered Tools ======")
    for tool in tool_registry.list_tools():
        print(tool.name)
