from dataclasses import dataclass
from uuid import uuid4

from sqlalchemy.orm import Session

from research_os.chea import (
    AssuranceClass,
    BrokerOutcome,
    Capability,
    DataBoundary,
    EvidenceRequirements,
    ExecutionEnvelope,
    ResourceLimits,
    RuntimeBroker,
    WorkflowContext,
)
from research_os.constitution import ConstitutionalRuntime, WorkflowRequest
from research_os.domain.errors import ValidationError

from .ai_provider import AIProvider, AIResearchRequest
from .chea_ai_adapter import AIProviderRuntimeAdapter
from .research_service import ResearchService
from .workflow_models import ResearchSource


@dataclass(frozen=True)
class WorkflowResult:
    execution_id: str
    publication_id: int
    receipt_id: int


class ResearchWorkflowService:
    """Run a governed research pipeline within the caller's transaction."""

    def __init__(
        self,
        session: Session,
        ai_provider: AIProvider,
        runtime: ConstitutionalRuntime | None = None,
    ):
        self.research = ResearchService(session)
        self.ai_provider = ai_provider
        self.runtime = runtime or ConstitutionalRuntime()

    def run(
        self,
        *,
        project_id: int,
        question: str,
        source_ids: list[int],
        model: str,
        max_output_tokens: int,
        workflow_version: str,
        publication_title: str,
        actor_id: str = "research-os-workflow",
    ) -> WorkflowResult:
        request = self.runtime.authorize(
            WorkflowRequest(
                project_id,
                question,
                self.ai_provider.provider_id,
                model,
                max_output_tokens,
            )
        )
        if self.runtime.constraints.require_sources and not source_ids:
            raise ValidationError("At least one source is required")

        self.research._project(project_id)
        sources = [self.research._owned(self.research.uow.sources, item, project_id) for item in source_ids]
        inputs = [
            ResearchSource(
                id=source.id,
                title=source.title,
                location=source.location,
                content=str(source.source_metadata.get("content", "")),
            )
            for source in sources
        ]
        if any(not source.content.strip() for source in inputs):
            raise ValidationError("Every workflow source must include metadata.content")

        self.research._event(
            project_id,
            "CONSTITUTIONAL_EXECUTION_STARTED",
            "project",
            project_id,
            {
                "ai_provider": self.ai_provider.provider_id,
                "model": model,
                "source_ids": source_ids,
                "workflow_version": workflow_version,
            },
        )
        research_question = self.research.create_question(project_id, question, "in_progress")
        ai_request = AIResearchRequest(
            question=request.question,
            sources=inputs,
            model=request.model,
            max_output_tokens=request.max_output_tokens,
        )
        capability = Capability(
            id="model.research.generate",
            scope=f"project:{project_id}",
            constraints={"provider": self.ai_provider.provider_id, "model": model},
        )
        envelope = ExecutionEnvelope(
            ee_id=f"ee-{uuid4()}",
            authorization_id=f"ccr-{uuid4()}",
            actor_id=actor_id,
            purpose=question,
            capabilities_requested=[capability],
            capabilities_granted=[capability],
            resource_limits=ResourceLimits(max_wall_clock_ms=120_000),
            data_boundaries=[
                DataBoundary(
                    id=f"project:{project_id}",
                    classification="project-research",
                    allowed_operations=["read-approved-sources", "write-derived-research"],
                )
            ],
            constitutional_version="ResearchOS-Constitution-0.1",
            policy_pack_version=f"ResearchWorkflow-{workflow_version}",
            evidence_requirements=EvidenceRequirements(
                minimum_assurance_class=AssuranceClass.LOCAL_PROCESS,
                require_deterministic_trace=False,
                require_attestation=False,
                require_full_tool_trace=False,
            ),
            workflow_context=WorkflowContext(
                workflow_id=workflow_version,
                project_id=str(project_id),
                tags=["research", "evidence-first"],
                extra={"source_ids": source_ids},
            ),
            issued_by="ConstitutionalAgentRuntime",
        )
        execution = RuntimeBroker([AIProviderRuntimeAdapter(self.ai_provider)]).execute(
            envelope, ai_request
        )
        if execution.record.outcome != BrokerOutcome.COMPLETED or execution.output is None:
            raise ValidationError("CHEA execution is indeterminate; research output was not committed")
        draft = execution.output
        allowed_source_ids = set(source_ids)
        if any(item.source_id not in allowed_source_ids for item in draft.evidence):
            raise ValidationError("Model output cited a source outside the governed source set")

        evidence = [
            self.research.create_evidence(
                project_id,
                item.source_id,
                item.content,
                item.kind,
                {
                    "relevance": item.relevance,
                    "ai_provider": self.ai_provider.provider_id,
                    "model": model,
                },
            )
            for item in draft.evidence
        ]
        claim_records = []
        verification_records = []
        for claim in draft.claims:
            if not claim.evidence_indexes or any(
                index < 0 or index >= len(evidence) for index in claim.evidence_indexes
            ):
                raise ValidationError("Claim references an invalid evidence index")
            primary = evidence[claim.evidence_indexes[0]]
            record = self.research.create_claim(
                project_id,
                primary.id,
                claim.text,
                metadata={
                    "confidence": claim.confidence,
                    "evidence_ids": [evidence[index].id for index in claim.evidence_indexes],
                    "ai_provider": self.ai_provider.provider_id,
                    "model": model,
                },
            )
            claim_records.append(record)
            self.research.create_analysis(
                project_id,
                record.id,
                "provider-structured-synthesis",
                claim.analysis,
                {"ai_provider": self.ai_provider.provider_id, "model": model},
            )
            verification_records.append(
                self.research.create_verification(
                    project_id,
                    record.id,
                    claim.verdict,
                    claim.verification_details,
                    {
                        "confidence": claim.confidence,
                        "ai_provider": self.ai_provider.provider_id,
                        "model": model,
                    },
                )
            )

        publication = self.research.create_publication(
            project_id,
            publication_title,
            report_text=draft.report_markdown,
            metadata={
                "ai_provider": self.ai_provider.provider_id,
                "model": model,
                "workflow_version": workflow_version,
                "chea_envelope_id": envelope.ee_id,
                "chea_bsr_id": execution.selection.bsr_id,
                "chea_cer_id": execution.record.cer_id,
            },
        )
        research_question.status = "completed"
        self.research._event(
            project_id,
            "QUESTION_COMPLETED",
            "question",
            research_question.id,
            {"publication_id": publication.id},
        )
        receipt = self.research.issue_receipt(
            project_id,
            question,
            model,
            workflow_version,
            draft.report_markdown,
            {
                "question_id": research_question.id,
                "ai_provider": self.ai_provider.provider_id,
                "source_ids": source_ids,
                "evidence_ids": [item.id for item in evidence],
                "claim_ids": [item.id for item in claim_records],
                "verification_ids": [item.id for item in verification_records],
                "publication_id": publication.id,
                "chea": {
                    "execution_envelope": execution.envelope.model_dump(mode="json"),
                    "broker_selection_record": execution.selection.model_dump(mode="json"),
                    "constitutional_execution_record": execution.record.model_dump(mode="json"),
                },
            },
            draft.warnings,
            draft.limitations,
            execution_id=execution.record.cer_id,
        )
        self.research._event(
            project_id,
            "CONSTITUTIONAL_EXECUTION_COMPLETED",
            "publication",
            publication.id,
            {"execution_id": receipt.execution_id, "receipt_id": receipt.id},
        )
        return WorkflowResult(receipt.execution_id, publication.id, receipt.id)
