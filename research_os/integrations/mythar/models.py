from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class MytharContext(BaseModel):
    source_language: Literal["mythar"] = "mythar"
    compiler_version: str = Field(min_length=1)
    line: int = Field(default=1, ge=1)
    column: int = Field(default=1, ge=1)


class MytharMetadata(BaseModel):
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    notes: list[str] = Field(default_factory=list)
    provenance: dict[str, Any] = Field(default_factory=dict)


class MytharArgument(BaseModel):
    role: str = Field(min_length=1)
    root: str = Field(min_length=1)
    semantic_class: str = Field(alias="class", min_length=1)
    domain: str = Field(min_length=1)
    intent: str = Field(min_length=1)


class MytharISF(BaseModel):
    """Mythar Intermediate Semantic Form v0.4 boundary contract."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    version: Literal["0.4"]
    root: str = Field(min_length=1)
    canonical: bool
    semantic_class: str = Field(alias="class", min_length=1)
    domain: str = Field(min_length=1)
    intent: str = Field(min_length=1)
    operators: list[str] = Field(default_factory=list)
    arguments: list[MytharArgument] = Field(default_factory=list)
    context: MytharContext
    metadata: MytharMetadata = Field(default_factory=MytharMetadata)

