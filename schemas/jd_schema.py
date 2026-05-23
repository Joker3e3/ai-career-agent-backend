from pydantic import BaseModel
from typing import List


class JDAnalysis(BaseModel):

    role_title: str

    required_skills: List[str]

    preferred_skills: List[str]

    frontend_skills: List[str]

    backend_skills: List[str]

    ai_skills: List[str]

    infra_skills: List[str]

    soft_skills: List[str]

    responsibilities: List[str]