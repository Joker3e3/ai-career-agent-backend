from pydantic import BaseModel
from typing import List


# Deprecated:
# 旧版固定 reflection/retry 节点使用固定的 prompt 模板进行反思和生成新的 query，已被 ReAct-style execute_react_action 替代。
# 当前 graph 不再连接该 node，仅保留用于对比历史实现。
class RetryQuery(BaseModel):
    dimension: str
    reason: str
    retry_query: str
    keywords: List[str]


class ReflectionResult(BaseModel):
    need_retry: bool
    retry_queries: List[RetryQuery]