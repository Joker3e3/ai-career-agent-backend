from dataclasses import dataclass
import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)


@dataclass
class ToolDefinition:
    name: str
    tool_type: str
    description: str
    func: Callable[..., Any]


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition):
        if tool.name in self._tools:
            logger.warning(
                "Tool already registered: %s",
                tool.name,
            )
            return

        self._tools[tool.name] = tool

    def get(self, name: str) -> ToolDefinition:
        if name not in self._tools:
            raise ValueError(f"Tool not found: {name}")

        return self._tools[name]

    def list_tools(self) -> list[ToolDefinition]:
        return list(self._tools.values())


tool_registry = ToolRegistry()
