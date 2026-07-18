from dataclasses import dataclass

from sqlalchemy.orm import Session

from research_os.constitution import ConstitutionalRuntime, WorkflowRequest
from research_os.domain.errors import ValidationError

from .ai_provider import AIProvider, AIResearchRequest
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
        draft = self.ai_provider.generate_research(
            AIResearchRequest(
                question=request.question,
                sources=inputs,
                model=request.model,
                max_output_tokens=request.max_output_tokens,
            )
        )
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
            },
            draft.warnings,
            draft.limitations,
        )
        self.research._event(
            project_id,
            "CONSTITUTIONAL_EXECUTION_COMPLETED",
            "publication",
            publication.id,
            {"execution_id": receipt.execution_id, "receipt_id": receipt.id},
        )
        return WorkflowResult(receipt.execution_id, publication.id, receipt.id)
