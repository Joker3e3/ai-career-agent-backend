from tools.tool_registry import tool_registry


def call_tool(
    tool_name: str,
    **kwargs,
):
    tool = tool_registry.get(tool_name)

    return tool.func(**kwargs)
