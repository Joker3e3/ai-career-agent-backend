from typing import Literal
from pydantic import BaseModel


class ToolInput(BaseModel):
    query: str
    keywords: list[str] = []


class ReactDecision(BaseModel):
    decision: Literal["continue", "act"]
    thought: str
    tool_name: str | None = None
    tool_input: ToolInput | None = None
