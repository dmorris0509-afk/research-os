from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, model_validator


def utcnow() -> datetime:
    return datetime.now(UTC)


class AssuranceClass(StrEnum):
    LOCAL_PROCESS = "LOCAL_PROCESS"
    ISOLATED_SANDBOX = "ISOLATED_SANDBOX"
    HARDWARE_ATTESTED = "HARDWARE_ATTESTED"
    MULTIPARTY_ATTESTED = "MULTIPARTY_ATTESTED"


ASSURANCE_RANK = {item: rank for rank, item in enumerate(AssuranceClass)}


class BrokerOutcome(StrEnum):
    COMPLETED = "COMPLETED"
    DENIED = "DENIED"
    INDETERMINATE = "INDETERMINATE"


class Capability(BaseModel):
    id: str = Field(min_length=1)
    scope: str | None = None
    constraints: dict[str, Any] = Field(default_factory=dict)


class ResourceLimits(BaseModel):
    max_cpu_seconds: float | None = Field(default=None, gt=0)
    max_wall_clock_ms: int | None = Field(default=None, gt=0)
    max_memory_mb: int | None = Field(default=None, gt=0)
    max_gpu_seconds: float | None = Field(default=None, gt=0)
    max_cost_usd: float | None = Field(default=None, ge=0)


class DataBoundary(BaseModel):
    id: str = Field(min_length=1)
    classification: str | None = None
    allowed_operations: list[str] = Field(default_factory=list)


class EvidenceRequirements(BaseModel):
    minimum_assurance_class: AssuranceClass
    require_deterministic_trace: bool = False
    require_attestation: bool = False
    require_full_tool_trace: bool = False


class WorkflowContext(BaseModel):
    workflow_id: str | None = None
    step_id: str | None = None
    project_id: str | None = None
    repo_id: str | None = None
    tags: list[str] = Field(default_factory=list)
    extra: dict[str, Any] = Field(default_factory=dict)


class ExecutionEnvelope(BaseModel):
    ee_id: str = Field(min_length=1)
    authorization_id: str = Field(min_length=1)
    actor_id: str = Field(min_length=1)
    principal_id: str | None = None
    delegated_authority: str | None = None
    purpose: str = Field(min_length=1)
    capabilities_requested: list[Capability]
    capabilities_granted: list[Capability]
    resource_limits: ResourceLimits = Field(default_factory=ResourceLimits)
    data_boundaries: list[DataBoundary]
    constitutional_version: str = Field(min_length=1)
    policy_pack_version: str = Field(min_length=1)
    evidence_requirements: EvidenceRequirements
    workflow_context: WorkflowContext | None = None
    created_at: datetime = Field(default_factory=utcnow)
    issued_by: str = Field(min_length=1)
    broker_hints: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def grants_must_be_requested(self):
        requested = {item.id for item in self.capabilities_requested}
        granted = {item.id for item in self.capabilities_granted}
        if not granted.issubset(requested):
            raise ValueError("Granted capabilities must be a subset of requested capabilities")
        return self


class RuntimeAdapterDescriptor(BaseModel):
    adapter_id: str = Field(min_length=1)
    adapter_version: str = Field(min_length=1)
    capabilities_supported: list[str]
    isolation_level: str = Field(min_length=1)
    evidence_fidelity_class: AssuranceClass
    security_properties: list[str] = Field(default_factory=list)
    conformance_version: str = Field(min_length=1)
    health_status: str = "healthy"
    attestation_support: bool = False


class CandidateAdapter(BaseModel):
    adapter_id: str
    adapter_version: str
    capability_match: bool
    assurance_match: bool
    health_match: bool
    selected: bool = False
    rejection_reasons: list[str] = Field(default_factory=list)


class BrokerSelectionRecord(BaseModel):
    bsr_id: str
    ee_id: str
    candidate_adapters: list[CandidateAdapter]
    capability_match: list[str]
    policy_constraints: list[str]
    selection_rationale: str
    fallback_rules: list[str]
    fallback_used: bool
    broker_version: str
    policy_pack_version: str


class LifecycleEvent(BaseModel):
    event: str
    timestamp: datetime = Field(default_factory=utcnow)
    details: dict[str, Any] = Field(default_factory=dict)


class AdapterExecutionResult(BaseModel):
    output: Any = None
    assurance_class: AssuranceClass
    evidence_bundle_refs: list[str] = Field(default_factory=list)
    lifecycle_events: list[LifecycleEvent] = Field(default_factory=list)
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    model_calls: list[dict[str, Any]] = Field(default_factory=list)
    external_service_calls: list[dict[str, Any]] = Field(default_factory=list)
    resource_consumption: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    exceptions: list[str] = Field(default_factory=list)
    retries: list[dict[str, Any]] = Field(default_factory=list)
    policy_interventions: list[dict[str, Any]] = Field(default_factory=list)
    conformance_claims: list[str] = Field(default_factory=list)
    cryptographic_attestation: dict[str, Any] | None = None


class ConstitutionalExecutionRecord(BaseModel):
    cer_id: str
    cer_schema_version: str = "0.1"
    outcome: BrokerOutcome
    authorization_id: str
    bsr_id: str
    actor_id: str
    principal_id: str | None = None
    delegated_authority: str | None = None
    capabilities_requested: list[Capability]
    capabilities_granted: list[Capability]
    runtime_selected: RuntimeAdapterDescriptor
    selection_rationale: str
    input_artifact_hashes: list[str]
    protected_data_classifications: list[str]
    execution_timestamps: dict[str, datetime]
    lifecycle_events: list[LifecycleEvent]
    tool_calls: list[dict[str, Any]]
    model_calls: list[dict[str, Any]]
    external_service_calls: list[dict[str, Any]]
    resource_consumption: dict[str, Any]
    resource_limits: ResourceLimits
    output_artifact_hashes: list[str]
    warnings: list[str]
    exceptions: list[str]
    retries: list[dict[str, Any]]
    policy_interventions: list[dict[str, Any]]
    verification_results: list[dict[str, Any]]
    conformance_claims: list[str]
    evidence_bundle_refs: list[str]
    predecessor_links: list[str] = Field(default_factory=list)
    successor_links: list[str] = Field(default_factory=list)
    assurance_class: AssuranceClass
    cryptographic_attestation: dict[str, Any] | None = None


class BrokerExecution(BaseModel):
    envelope: ExecutionEnvelope
    selection: BrokerSelectionRecord
    record: ConstitutionalExecutionRecord
    output: Any = None

