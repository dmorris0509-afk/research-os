import hashlib
import uuid
from typing import Any, Literal

from sqlalchemy import select
from sqlalchemy.orm import Session

from research_os.domain.errors import ConflictError, ValidationError
from research_os.domain.models import Claim, ResearchEvent
from research_os.domain.repositories import UnitOfWork

QuestionStatus = Literal["open", "in_progress", "completed"]
ClaimStatus = Literal["unverified", "verified", "rejected"]
VerificationResult = Literal["pass", "fail", "inconclusive"]


class ResearchService:
    def __init__(self, session: Session):
        self.uow = UnitOfWork(session)

    def _project(self, project_id: int):
        return self.uow.projects.require(project_id)

    def _owned(self, repository, entity_id: int, project_id: int):
        entity = repository.require(entity_id)
        if entity.project_id != project_id:
            raise ConflictError("Entity does not belong to the requested project")
        return entity

    def _event(self, project_id: int, type: str, entity_type: str, entity_id: int, payload=None):
        return self.uow.events.add(
            project_id=project_id,
            type=type,
            entity_type=entity_type,
            entity_id=entity_id,
            payload=payload or {},
        )

    def create_project(self, name: str, description: str | None = None):
        if not name.strip():
            raise ValidationError("Project name is required")
        project = self.uow.projects.add(name=name.strip(), description=description)
        self._event(project.id, "PROJECT_CREATED", "project", project.id, {"name": project.name})
        return project

    def create_question(self, project_id: int, text: str, status: QuestionStatus = "open"):
        self._project(project_id)
        question = self.uow.questions.add(project_id=project_id, text=text.strip(), status=status)
        self._event(project_id, "QUESTION_ADDED", "question", question.id)
        return question

    def create_source(self, project_id: int, kind: str, location: str, title=None, metadata=None):
        self._project(project_id)
        source = self.uow.sources.add(
            project_id=project_id, kind=kind, location=location, title=title, source_metadata=metadata or {}
        )
        self._event(project_id, "SOURCE_INGESTED", "source", source.id, {"kind": kind, "location": location})
        return source

    def create_evidence(self, project_id: int, source_id: int, content: str, kind: str, metadata=None):
        self._owned(self.uow.sources, source_id, project_id)
        evidence = self.uow.evidence.add(
            project_id=project_id,
            source_id=source_id,
            content=content,
            kind=kind,
            evidence_metadata=metadata or {},
        )
        self._event(project_id, "EVIDENCE_EXTRACTED", "evidence", evidence.id, {"source_id": source_id})
        return evidence

    def create_claim(
        self, project_id: int, evidence_id: int, text: str, status: ClaimStatus = "unverified", metadata=None
    ):
        self._owned(self.uow.evidence, evidence_id, project_id)
        claim = self.uow.claims.add(
            project_id=project_id,
            evidence_id=evidence_id,
            text=text,
            status=status,
            claim_metadata=metadata or {},
        )
        self._event(project_id, "CLAIM_GENERATED", "claim", claim.id, {"evidence_id": evidence_id})
        return claim

    def create_analysis(self, project_id: int, claim_id: int, method: str, notes=None, metadata=None):
        self._owned(self.uow.claims, claim_id, project_id)
        analysis = self.uow.analyses.add(
            project_id=project_id,
            claim_id=claim_id,
            method=method,
            notes=notes,
            analysis_metadata=metadata or {},
        )
        self._event(
            project_id, "ANALYSIS_CREATED", "analysis", analysis.id, {"claim_id": claim_id, "method": method}
        )
        return analysis

    def create_verification(
        self, project_id: int, claim_id: int, result: VerificationResult, details=None, metadata=None
    ):
        claim: Claim = self._owned(self.uow.claims, claim_id, project_id)
        verification = self.uow.verifications.add(
            project_id=project_id,
            claim_id=claim_id,
            result=result,
            details=details,
            verification_metadata=metadata or {},
        )
        claim.status = {"pass": "verified", "fail": "rejected", "inconclusive": "unverified"}[result]
        self._event(
            project_id,
            "CLAIM_VERIFIED",
            "verification",
            verification.id,
            {"claim_id": claim_id, "result": result},
        )
        return verification

    def create_publication(
        self, project_id: int, title: str, report_path=None, report_text=None, metadata=None
    ):
        self._project(project_id)
        if not report_path and not report_text:
            raise ValidationError("Publication requires report_path or report_text")
        publication = self.uow.publications.add(
            project_id=project_id,
            title=title,
            report_path=report_path,
            report_text=report_text,
            publication_metadata=metadata or {},
        )
        self._event(project_id, "REPORT_PUBLISHED", "publication", publication.id, {"title": title})
        return publication

    def issue_receipt(
        self,
        project_id: int,
        question: str,
        model: str,
        workflow_version: str,
        report_text: str,
        evidence_bundle: dict[str, Any],
        warnings=None,
        limitations=None,
    ):
        self._project(project_id)
        receipt = self.uow.receipts.add(
            project_id=project_id,
            execution_id=str(uuid.uuid4()),
            question=question,
            gpt_model=model,
            workflow_version=workflow_version,
            evidence_bundle=evidence_bundle,
            warnings=warnings or [],
            limitations=limitations or [],
            report_hash=hashlib.sha256(report_text.encode()).hexdigest(),
        )
        self._event(
            project_id,
            "RESEARCH_RECEIPT_ISSUED",
            "receipt",
            receipt.id,
            {"execution_id": receipt.execution_id, "report_hash": receipt.report_hash},
        )
        return receipt

    def list_entities(self, entity: str, project_id: int, limit=100, offset=0):
        self._project(project_id)
        repository = getattr(self.uow, entity)
        return repository.list(project_id=project_id, limit=limit, offset=offset)

    def delete_entity(self, entity: str, project_id: int, entity_id: int):
        repository = getattr(self.uow, entity)
        self._owned(repository, entity_id, project_id)
        repository.delete(entity_id)

    def timeline(self, project_id: int, limit=200, offset=0):
        self._project(project_id)
        statement = (
            select(ResearchEvent)
            .where(ResearchEvent.project_id == project_id)
            .order_by(ResearchEvent.created_at, ResearchEvent.id)
            .offset(offset)
            .limit(limit)
        )
        return tuple(self.uow.session.scalars(statement))
