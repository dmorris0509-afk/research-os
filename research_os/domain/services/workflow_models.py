from typing import Literal

from pydantic import BaseModel, Field


class EvidenceDraft(BaseModel):
    source_id: int
    content: str = Field(min_length=1)
    kind: str = Field(default="excerpt", min_length=1, max_length=40)
    relevance: float = Field(ge=0, le=1)


class ClaimDraft(BaseModel):
    evidence_indexes: list[int] = Field(min_length=1)
    text: str = Field(min_length=1)
    analysis: str = Field(min_length=1)
    verdict: Literal["pass", "fail", "inconclusive"]
    verification_details: str = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)


class ResearchDraft(BaseModel):
    evidence: list[EvidenceDraft]
    claims: list[ClaimDraft]
    report_markdown: str = Field(min_length=1)
    warnings: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(min_length=1)


class ResearchSource(BaseModel):
    id: int
    title: str | None
    location: str
    content: str
