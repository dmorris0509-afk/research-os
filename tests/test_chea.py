from typing import Any

import pytest
from pydantic import ValidationError as PydanticValidationError

from research_os.chea import (
    AdapterExecutionResult,
    AssuranceClass,
    BrokerOutcome,
    Capability,
    DataBoundary,
    EvidenceRequirements,
    ExecutionDenied,
    ExecutionEnvelope,
    ResourceLimits,
    RuntimeAdapterDescriptor,
    RuntimeBroker,
)


class FakeAdapter:
    def __init__(
        self,
        adapter_id: str,
        *,
        capabilities: list[str] | None = None,
        assurance: AssuranceClass = AssuranceClass.LOCAL_PROCESS,
        result_assurance: AssuranceClass | None = None,
        resource_consumption: dict[str, Any] | None = None,
        healthy: bool = True,
    ):
        self._descriptor = RuntimeAdapterDescriptor(
            adapter_id=adapter_id,
            adapter_version="1.0.0",
            capabilities_supported=capabilities or ["research.execute"],
            isolation_level="test",
            evidence_fidelity_class=assurance,
            conformance_version="CHEA-0.1",
            health_status="healthy" if healthy else "degraded",
        )
        self.result_assurance = result_assurance or assurance
        self.resource_consumption = resource_consumption or {}

    @property
    def descriptor(self):
        return self._descriptor

    def execute(self, _envelope, payload):
        return AdapterExecutionResult(
            output={"echo": payload},
            assurance_class=self.result_assurance,
            resource_consumption=self.resource_consumption,
            evidence_bundle_refs=["evidence:test"],
            conformance_claims=["CHEA-Level-0"],
        )


def envelope(**overrides):
    capability = Capability(id="research.execute", scope="project:1")
    values = {
        "ee_id": "ee-test",
        "authorization_id": "ccr-test",
        "actor_id": "actor-test",
        "purpose": "Run governed research",
        "capabilities_requested": [capability],
        "capabilities_granted": [capability],
        "resource_limits": ResourceLimits(max_wall_clock_ms=1_000),
        "data_boundaries": [DataBoundary(id="project:1", classification="internal")],
        "constitutional_version": "constitution-1",
        "policy_pack_version": "policy-1",
        "evidence_requirements": EvidenceRequirements(
            minimum_assurance_class=AssuranceClass.LOCAL_PROCESS
        ),
        "issued_by": "test-runtime",
    }
    values.update(overrides)
    return ExecutionEnvelope(**values)


def test_broker_selection_is_deterministic_and_records_candidates():
    broker = RuntimeBroker([FakeAdapter("z-adapter"), FakeAdapter("a-adapter")])

    first = broker.execute(envelope(), {"question": "why"})
    second = broker.execute(envelope(), {"question": "why"})

    assert first.record.runtime_selected.adapter_id == "a-adapter"
    assert second.record.runtime_selected.adapter_id == "a-adapter"
    assert first.record.outcome == BrokerOutcome.COMPLETED
    assert [item.adapter_id for item in first.selection.candidate_adapters] == [
        "a-adapter",
        "z-adapter",
    ]
    assert first.record.authorization_id == first.envelope.authorization_id
    assert first.record.bsr_id == first.selection.bsr_id


def test_broker_denies_when_no_adapter_meets_capabilities():
    broker = RuntimeBroker([FakeAdapter("limited", capabilities=["other.capability"])])

    with pytest.raises(ExecutionDenied) as error:
        broker.execute(envelope(), {})

    assert error.value.selection.candidate_adapters[0].capability_match is False
    assert "missing capabilities" in error.value.selection.candidate_adapters[0].rejection_reasons[0]


def test_broker_prevents_assurance_inflation():
    adapter = FakeAdapter(
        "inflated",
        assurance=AssuranceClass.LOCAL_PROCESS,
        result_assurance=AssuranceClass.HARDWARE_ATTESTED,
    )

    result = RuntimeBroker([adapter]).execute(envelope(), {})

    assert result.record.outcome == BrokerOutcome.INDETERMINATE
    assert result.record.assurance_class == AssuranceClass.LOCAL_PROCESS
    assert result.output is None
    assert result.record.policy_interventions[0]["type"] == "ASSURANCE_CLAMP"


def test_resource_overrun_is_indeterminate_and_output_is_withheld():
    adapter = FakeAdapter("expensive", resource_consumption={"wall_clock_ms": 1_001})

    result = RuntimeBroker([adapter]).execute(envelope(), {})

    assert result.record.outcome == BrokerOutcome.INDETERMINATE
    assert result.output is None
    assert any(item["type"] == "RESOURCE_LIMIT_EXCEEDED" for item in result.record.policy_interventions)


def test_envelope_rejects_capability_escalation():
    with pytest.raises(PydanticValidationError):
        envelope(capabilities_granted=[Capability(id="admin.unrequested")])

