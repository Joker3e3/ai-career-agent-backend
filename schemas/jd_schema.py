from typing import List
from pydantic import BaseModel

# role_title：岗位名称
# role_category：岗位类别，例如 tech / hr / admin / sales / product / finance / other
# requirements：岗位能力要求，不再写死前端/后端/AI
# responsibilities：核心职责
# background_requirements：学历、经验年限、行业背景等要求


class JobRequirement(BaseModel):
    dimension: str
    priority: str
    keywords: List[str]
    description: str


class JDAnalysis(BaseModel):
    role_title: str
    role_category: str
    requirements: List[JobRequirement]
    responsibilities: List[str]
    background_requirements: List[str]
