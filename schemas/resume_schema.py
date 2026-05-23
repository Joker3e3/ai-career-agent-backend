from pydantic import BaseModel
from typing import List


class SkillEvidence(BaseModel):
    skill: str
    evidence: str


class ProjectExperience(BaseModel):
    name: str
    description: str
    skills: List[str]


class ResumeProfile(BaseModel):
    frontend_skills: List[SkillEvidence]
    backend_skills: List[SkillEvidence]
    ai_skills: List[SkillEvidence]
    infra_skills: List[SkillEvidence]
    projects: List[ProjectExperience]
    education: str
    summary: str