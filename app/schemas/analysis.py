from typing import Literal

from pydantic import BaseModel, Field


class LogEvidence(BaseModel):
    line_number: int = Field(ge=1)
    message: str = Field(min_length=1)


class LogAnalysisResponse(BaseModel):
    summary: str = Field(min_length=1)
    likely_causes: list[str]
    evidence: list[LogEvidence]
    recommended_steps: list[str]
    confidence: Literal["low", "medium", "high"]
    limitations: list[str]