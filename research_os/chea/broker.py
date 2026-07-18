import hashlib
import json
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel

from research_os.domain.errors import ValidationError

from .adapter import RuntimeAdapter
from .models import (
    ASSURANCE_RANK,
    AdapterExecutionResult,
    AssuranceClass,
    BrokerExecution,
    BrokerOutcome,
    BrokerSelectionRecord,
    CandidateAdapter,
    ConstitutionalExecutionRecord,
    ExecutionEnvelope,
    LifecycleEvent,
)


class ExecutionDenied(ValidationError):
    def __init__(self, message: str, selection: BrokerSelectionRecord):
        super().__init__(message)
        self.selection = selection


def _jsonable(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def artifact_hash(value: Any) -> str:
    encoded = json.dumps(_jsonable(value), sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(encoded).hexdigest()


class RuntimeBroker:
    """Deterministic, policy-constrained CHEA dispatcher."""

    def __init__(self, adapters: list[RuntimeAdapter], version: str = "0.1.0"):
        identities = [(item.descriptor.adapter_id, item.descriptor.adapter_version) for item in adapters]
        if len(identities) != len(set(identities)):
            raise ValueError("Runtime adapter identities must be unique")
        self.adapters = tuple(sorted(adapters, key=lambda item: identities_key(item)))
        self.version = version

    def select(self, envelope: ExecutionEnvelope) -> tuple[RuntimeAdapter, BrokerSelectionRecord]:
        required = {item.id for item in envelope.capabilities_granted}
        minimum = envelope.evidence_requirements.minimum_assurance_class
        candidates: list[CandidateAdapter] = []
        conformant: list[RuntimeAdapter] = []

        for adapter in self.adapters:
            descriptor = adapter.descriptor
            missing = sorted(required - set(descriptor.capabilities_supported))
            assurance_match = ASSURANCE_RANK[descriptor.evidence_fidelity_class] >= ASSURANCE_RANK[minimum]
            health_match = descriptor.health_status == "healthy"
            attestation_match = (
                not envelope.evidence_requirements.require_attestation or descriptor.attestation_support
            )
            reasons = []
            if missing:
                reasons.append(f"missing capabilities: {', '.join(missing)}")
            if not assurance_match:
                reasons.append("insufficient assurance class")
            if not health_match:
                reasons.append(f"health status is {descriptor.health_status}")
            if not attestation_match:
                reasons.append("attestation is required but unsupported")
            candidate = CandidateAdapter(
                adapter_id=descriptor.adapter_id,
                adapter_version=descriptor.adapter_version,
                capability_match=not missing,
                assurance_match=assurance_match and attestation_match,
                health_match=health_match,
                rejection_reasons=reasons,
            )
            candidates.append(candidate)
            if not reasons:
                conformant.append(adapter)

        selected = min(
            conformant,
            key=lambda item: (
                ASSURANCE_RANK[item.descriptor.evidence_fidelity_class],
                item.descriptor.adapter_id,
                item.descriptor.adapter_version,
            ),
            default=None,
        )
        if selected:
            for item in candidates:
                item.selected = (
                    item.adapter_id == selected.descriptor.adapter_id
                    and item.adapter_version == selected.descriptor.adapter_version
                )
            rationale = (
                "Selected the lexically first adapter at the lowest conformant assurance class; "
                "broker hints cannot override policy constraints."
            )
        else:
            rationale = "No adapter satisfied the granted capabilities and evidence requirements."

        selection = BrokerSelectionRecord(
            bsr_id=f"bsr-{uuid4()}",
            ee_id=envelope.ee_id,
            candidate_adapters=candidates,
            capability_match=sorted(required),
            policy_constraints=[
                f"minimum_assurance={minimum.value}",
                f"attestation_required={envelope.evidence_requirements.require_attestation}",
                "fail_closed=true",
            ],
            selection_rationale=rationale,
            fallback_rules=["fallback only to another fully conformant adapter"],
            fallback_used=False,
            broker_version=self.version,
            policy_pack_version=envelope.policy_pack_version,
        )
        if selected is None:
            raise ExecutionDenied(
                "CHEA denied execution because no conformant adapter is available", selection
            )
        return selected, selection

    def execute(self, envelope: ExecutionEnvelope, payload: Any) -> BrokerExecution:
        adapter, selection = self.select(envelope)
        started = datetime.now(UTC)
        try:
            result = adapter.execute(envelope, payload)
        except Exception as exc:
            result = AdapterExecutionResult(
                assurance_class=AssuranceClass.LOCAL_PROCESS,
                exceptions=[f"{type(exc).__name__}: {exc}"],
                lifecycle_events=[LifecycleEvent(event="ADAPTER_EXCEPTION")],
            )
        completed = datetime.now(UTC)
        descriptor = adapter.descriptor
        outcome = BrokerOutcome.COMPLETED
        verification: list[dict[str, Any]] = []
        warnings = list(result.warnings)
        interventions = list(result.policy_interventions)

        claimed_rank = ASSURANCE_RANK[result.assurance_class]
        adapter_rank = ASSURANCE_RANK[descriptor.evidence_fidelity_class]
        minimum_rank = ASSURANCE_RANK[envelope.evidence_requirements.minimum_assurance_class]
        effective_assurance = result.assurance_class
        if claimed_rank > adapter_rank:
            effective_assurance = descriptor.evidence_fidelity_class
            outcome = BrokerOutcome.INDETERMINATE
            warnings.append("Adapter result claimed assurance above its registered evidence fidelity")
            interventions.append({"type": "ASSURANCE_CLAMP", "to": effective_assurance.value})
        if ASSURANCE_RANK[effective_assurance] < minimum_rank:
            outcome = BrokerOutcome.INDETERMINATE
            verification.append({"check": "minimum_assurance", "status": "failed"})
        else:
            verification.append({"check": "minimum_assurance", "status": "passed"})
        if envelope.evidence_requirements.require_attestation and not result.cryptographic_attestation:
            outcome = BrokerOutcome.INDETERMINATE
            verification.append({"check": "attestation", "status": "failed"})
        elif envelope.evidence_requirements.require_attestation:
            verification.append({"check": "attestation", "status": "passed"})
        if result.exceptions:
            outcome = BrokerOutcome.INDETERMINATE
            verification.append({"check": "adapter_exceptions", "status": "failed"})

        violations = _resource_violations(envelope, result)
        if violations:
            outcome = BrokerOutcome.INDETERMINATE
            interventions.extend({"type": "RESOURCE_LIMIT_EXCEEDED", "detail": item} for item in violations)
            verification.append({"check": "resource_limits", "status": "failed", "details": violations})
        else:
            verification.append({"check": "resource_limits", "status": "passed"})

        record = ConstitutionalExecutionRecord(
            cer_id=str(uuid4()),
            outcome=outcome,
            authorization_id=envelope.authorization_id,
            bsr_id=selection.bsr_id,
            actor_id=envelope.actor_id,
            principal_id=envelope.principal_id,
            delegated_authority=envelope.delegated_authority,
            capabilities_requested=envelope.capabilities_requested,
            capabilities_granted=envelope.capabilities_granted,
            runtime_selected=descriptor,
            selection_rationale=selection.selection_rationale,
            input_artifact_hashes=[artifact_hash(payload)],
            protected_data_classifications=sorted(
                {item.classification for item in envelope.data_boundaries if item.classification}
            ),
            execution_timestamps={"started_at": started, "completed_at": completed},
            lifecycle_events=[LifecycleEvent(event="BROKER_DISPATCHED", timestamp=started)]
            + result.lifecycle_events
            + [LifecycleEvent(event="BROKER_COMPLETED", timestamp=completed)],
            tool_calls=result.tool_calls,
            model_calls=result.model_calls,
            external_service_calls=result.external_service_calls,
            resource_consumption=result.resource_consumption,
            resource_limits=envelope.resource_limits,
            output_artifact_hashes=[artifact_hash(result.output)] if result.output is not None else [],
            warnings=warnings,
            exceptions=result.exceptions,
            retries=result.retries,
            policy_interventions=interventions,
            verification_results=verification,
            conformance_claims=result.conformance_claims,
            evidence_bundle_refs=result.evidence_bundle_refs,
            assurance_class=effective_assurance,
            cryptographic_attestation=result.cryptographic_attestation,
        )
        return BrokerExecution(
            envelope=envelope,
            selection=selection,
            record=record,
            output=result.output if outcome == BrokerOutcome.COMPLETED else None,
        )


def identities_key(adapter: RuntimeAdapter) -> tuple[str, str]:
    return adapter.descriptor.adapter_id, adapter.descriptor.adapter_version


def _resource_violations(
    envelope: ExecutionEnvelope, result: AdapterExecutionResult
) -> list[str]:
    checks = {
        "cpu_seconds": envelope.resource_limits.max_cpu_seconds,
        "wall_clock_ms": envelope.resource_limits.max_wall_clock_ms,
        "memory_mb": envelope.resource_limits.max_memory_mb,
        "gpu_seconds": envelope.resource_limits.max_gpu_seconds,
        "cost_usd": envelope.resource_limits.max_cost_usd,
    }
    violations = []
    for key, maximum in checks.items():
        consumed = result.resource_consumption.get(key)
        if maximum is not None and consumed is not None and consumed > maximum:
            violations.append(f"{key}={consumed} exceeds {maximum}")
    return violations
