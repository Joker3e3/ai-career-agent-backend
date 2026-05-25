from pydantic import BaseModel
from typing import List


# dimension：检索维度，例如 frontend / backend / ai / infra
# query：自然语言检索 query，偏向量检索
# keywords：关键词列表，偏 BM25 / hybrid 检索
class RetrievalQuery(BaseModel):
    dimension: str
    query: str
    keywords: List[str]


class QueryPlan(BaseModel):
    queries: List[RetrievalQuery]