from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=10_000)


class ProjectRead(ORMModel):
    id: int
    name: str
    description: str | None
    created_at: datetime


class QuestionCreate(BaseModel):
    text: str = Field(min_length=1, max_length=20_000)
    status: Literal["open", "in_progress", "completed"] = "open"


class QuestionRead(ORMModel):
    id: int
    project_id: int
    text: str
    status: str
    created_at: datetime


class SourceCreate(BaseModel):
    kind: str = Field(min_length=1, max_length=40)
    location: str = Field(min_length=1, max_length=2048)
    title: str | None = Field(default=None, max_length=500)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SourceRead(ORMModel):
    id: int
    project_id: int
    kind: str
    location: str
    title: str | None
    metadata: dict[str, Any] = Field(validation_alias="source_metadata")
    ingested_at: datetime


class EvidenceCreate(BaseModel):
    source_id: int = Field(gt=0)
    content: str = Field(min_length=1)
    kind: str = Field(min_length=1, max_length=40)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvidenceRead(ORMModel):
    id: int
    project_id: int
    source_id: int
    content: str
    kind: str
    metadata: dict[str, Any] = Field(validation_alias="evidence_metadata")
    extracted_at: datetime


class ClaimCreate(BaseModel):
    evidence_id: int = Field(gt=0)
    text: str = Field(min_length=1)
    status: Literal["unverified", "verified", "rejected"] = "unverified"
    metadata: dict[str, Any] = Field(default_factory=dict)


class ClaimRead(ORMModel):
    id: int
    project_id: int
    evidence_id: int
    text: str
    status: str
    created_at: datetime
    metadata: dict[str, Any] = Field(validation_alias="claim_metadata")


class AnalysisCreate(BaseModel):
    claim_id: int = Field(gt=0)
    method: str = Field(min_length=1, max_length=80)
    notes: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AnalysisRead(ORMModel):
    id: int
    project_id: int
    claim_id: int
    method: str
    notes: str | None
    created_at: datetime
    metadata: dict[str, Any] = Field(validation_alias="analysis_metadata")


class VerificationCreate(BaseModel):
    claim_id: int = Field(gt=0)
    result: Literal["pass", "fail", "inconclusive"]
    details: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class VerificationRead(ORMModel):
    id: int
    project_id: int
    claim_id: int
    result: str
    details: str | None
    verified_at: datetime
    metadata: dict[str, Any] = Field(validation_alias="verification_metadata")


class PublicationCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    report_path: str | None = Field(default=None, max_length=2048)
    report_text: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def require_report(self):
        if not self.report_path and not self.report_text:
            raise ValueError("report_path or report_text is required")
        return self


class PublicationRead(ORMModel):
    id: int
    project_id: int
    title: str
    report_path: str | None
    report_text: str | None
    published_at: datetime
    metadata: dict[str, Any] = Field(validation_alias="publication_metadata")


class EventRead(ORMModel):
    id: int
    project_id: int
    type: str
    entity_type: str
    entity_id: int
    payload: dict[str, Any]
    parent_event_id: int | None
    created_at: datetime


class ReceiptCreate(BaseModel):
    question: str = Field(min_length=1)
    model: str = Field(min_length=1, max_length=80)
    workflow_version: str = Field(min_length=1, max_length=40)
    report_text: str
    evidence_bundle: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class ReceiptRead(ORMModel):
    id: int
    project_id: int
    execution_id: str
    question: str
    gpt_model: str
    workflow_version: str
    evidence_bundle: dict[str, Any]
    warnings: list[str]
    limitations: list[str]
    report_hash: str
    created_at: datetime


class WorkflowExecute(BaseModel):
    question: str = Field(min_length=1, max_length=20_000)
    source_ids: list[int] = Field(min_length=1, max_length=100)
    model: Literal["gpt-5.6"] = "gpt-5.6"
    max_output_tokens: int = Field(default=8_000, ge=1, le=20_000)
    workflow_version: str = Field(default="1.0.0", min_length=1, max_length=40)
    publication_title: str = Field(min_length=1, max_length=500)


class WorkflowRead(BaseModel):
    execution_id: str
    publication_id: int
    receipt_id: int
