from pydantic import BaseModel
from typing import List


class MatchedSkill(BaseModel):
    skill: str
    evidence: str


class MatchResult(BaseModel):

    match_score: int

    matched_skills: List[MatchedSkill]

    missing_skills: List[str]

    strengths: List[str]

    risks: List[str]

    summary: str