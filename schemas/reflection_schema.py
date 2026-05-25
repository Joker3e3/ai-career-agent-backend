from pydantic import BaseModel
from typing import List


class RetryQuery(BaseModel):
    dimension: str
    reason: str
    retry_query: str
    keywords: List[str]


class ReflectionResult(BaseModel):
    need_retry: bool
    retry_queries: List[RetryQuery]