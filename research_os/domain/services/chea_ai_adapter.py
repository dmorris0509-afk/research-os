from time import perf_counter

from research_os.chea import (
    AdapterExecutionResult,
    AssuranceClass,
    ExecutionEnvelope,
    LifecycleEvent,
    RuntimeAdapterDescriptor,
)

from .ai_provider import AIProvider, AIResearchRequest


class AIProviderRuntimeAdapter:
    """Expose an AI provider through the replaceable CHEA adapter contract."""

    def __init__(self, provider: AIProvider):
        self.provider = provider

    @property
    def descriptor(self) -> RuntimeAdapterDescriptor:
        return RuntimeAdapterDescriptor(
            adapter_id=f"ai-provider:{self.provider.provider_id}",
            adapter_version="0.1.0",
            capabilities_supported=["model.research.generate"],
            isolation_level="hosted-provider-boundary",
            evidence_fidelity_class=AssuranceClass.LOCAL_PROCESS,
            security_properties=["provider-neutral-contract", "project-source-allow-list"],
            conformance_version="CHEA-0.1",
            health_status="healthy",
            attestation_support=False,
        )

    def execute(
        self, envelope: ExecutionEnvelope, payload: AIResearchRequest
    ) -> AdapterExecutionResult:
        started = perf_counter()
        draft = self.provider.generate_research(payload)
        elapsed_ms = round((perf_counter() - started) * 1000, 3)
        return AdapterExecutionResult(
            output=draft,
            assurance_class=AssuranceClass.LOCAL_PROCESS,
            lifecycle_events=[LifecycleEvent(event="MODEL_RESEARCH_GENERATED")],
            model_calls=[
                {
                    "provider": self.provider.provider_id,
                    "model": payload.model,
                    "max_output_tokens": payload.max_output_tokens,
                }
            ],
            external_service_calls=[{"service": self.provider.provider_id, "operation": "research"}],
            resource_consumption={"wall_clock_ms": elapsed_ms},
            conformance_claims=["CHEA-Level-0", "source-boundary-validated-by-workflow"],
        )

