from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from research_os.db import get_session
from research_os.domain.services import ResearchService, ResearchWorkflowService
from research_os.domain.services.ai_provider import AIProviderRegistry
from research_os.infrastructure import OpenAIResearchClient

from .auth import current_principal
from .schemas import (
    AnalysisCreate,
    AnalysisRead,
    ClaimCreate,
    ClaimRead,
    EventRead,
    EvidenceCreate,
    EvidenceRead,
    ProjectCreate,
    ProjectRead,
    PublicationCreate,
    PublicationRead,
    QuestionCreate,
    QuestionRead,
    ReceiptCreate,
    ReceiptRead,
    SourceCreate,
    SourceRead,
    VerificationCreate,
    VerificationRead,
    WorkflowExecute,
    WorkflowRead,
)

router = APIRouter(prefix="/api/v1", dependencies=[Depends(current_principal)])


def service(session: Session = Depends(get_session)) -> ResearchService:
    return ResearchService(session)


def ai_provider_registry() -> AIProviderRegistry:
    return AIProviderRegistry([OpenAIResearchClient()])


@router.post("/projects", response_model=ProjectRead, status_code=201)
def create_project(payload: ProjectCreate, svc: ResearchService = Depends(service)):
    return svc.create_project(payload.name, payload.description)


@router.get("/projects", response_model=list[ProjectRead])
def list_projects(limit: int = 100, offset: int = 0, svc: ResearchService = Depends(service)):
    return svc.uow.projects.list(limit=min(max(limit, 1), 200), offset=max(offset, 0))


@router.get("/projects/{project_id}", response_model=ProjectRead)
def get_project(project_id: int, svc: ResearchService = Depends(service)):
    return svc.uow.projects.require(project_id)


@router.delete("/projects/{project_id}", status_code=204)
def delete_project(project_id: int, svc: ResearchService = Depends(service)):
    svc.uow.projects.delete(project_id)
    return Response(status_code=204)


@router.post("/projects/{project_id}/questions", response_model=QuestionRead, status_code=201)
def create_question(project_id: int, body: QuestionCreate, svc: ResearchService = Depends(service)):
    return svc.create_question(project_id, body.text, body.status)


@router.get("/projects/{project_id}/questions", response_model=list[QuestionRead])
def list_questions(project_id: int, svc: ResearchService = Depends(service)):
    return svc.list_entities("questions", project_id)


@router.post("/projects/{project_id}/sources", response_model=SourceRead, status_code=201)
def create_source(project_id: int, body: SourceCreate, svc: ResearchService = Depends(service)):
    return svc.create_source(project_id, body.kind, body.location, body.title, body.metadata)


@router.get("/projects/{project_id}/sources", response_model=list[SourceRead])
def list_sources(project_id: int, svc: ResearchService = Depends(service)):
    return svc.list_entities("sources", project_id)


@router.post("/projects/{project_id}/evidence", response_model=EvidenceRead, status_code=201)
def create_evidence(project_id: int, body: EvidenceCreate, svc: ResearchService = Depends(service)):
    return svc.create_evidence(project_id, body.source_id, body.content, body.kind, body.metadata)


@router.get("/projects/{project_id}/evidence", response_model=list[EvidenceRead])
def list_evidence(project_id: int, svc: ResearchService = Depends(service)):
    return svc.list_entities("evidence", project_id)


@router.post("/projects/{project_id}/claims", response_model=ClaimRead, status_code=201)
def create_claim(project_id: int, body: ClaimCreate, svc: ResearchService = Depends(service)):
    return svc.create_claim(project_id, body.evidence_id, body.text, body.status, body.metadata)


@router.get("/projects/{project_id}/claims", response_model=list[ClaimRead])
def list_claims(project_id: int, svc: ResearchService = Depends(service)):
    return svc.list_entities("claims", project_id)


@router.post("/projects/{project_id}/analyses", response_model=AnalysisRead, status_code=201)
def create_analysis(project_id: int, body: AnalysisCreate, svc: ResearchService = Depends(service)):
    return svc.create_analysis(project_id, body.claim_id, body.method, body.notes, body.metadata)


@router.get("/projects/{project_id}/analyses", response_model=list[AnalysisRead])
def list_analyses(project_id: int, svc: ResearchService = Depends(service)):
    return svc.list_entities("analyses", project_id)


@router.post("/projects/{project_id}/verifications", response_model=VerificationRead, status_code=201)
def create_verification(project_id: int, body: VerificationCreate, svc: ResearchService = Depends(service)):
    return svc.create_verification(project_id, body.claim_id, body.result, body.details, body.metadata)


@router.get("/projects/{project_id}/verifications", response_model=list[VerificationRead])
def list_verifications(project_id: int, svc: ResearchService = Depends(service)):
    return svc.list_entities("verifications", project_id)


@router.post("/projects/{project_id}/publications", response_model=PublicationRead, status_code=201)
def create_publication(project_id: int, body: PublicationCreate, svc: ResearchService = Depends(service)):
    return svc.create_publication(project_id, body.title, body.report_path, body.report_text, body.metadata)


@router.get("/projects/{project_id}/publications", response_model=list[PublicationRead])
def list_publications(project_id: int, svc: ResearchService = Depends(service)):
    return svc.list_entities("publications", project_id)


@router.get("/projects/{project_id}/timeline", response_model=list[EventRead])
def timeline(project_id: int, svc: ResearchService = Depends(service)):
    return svc.timeline(project_id)


@router.post("/projects/{project_id}/receipts", response_model=ReceiptRead, status_code=201)
def create_receipt(project_id: int, body: ReceiptCreate, svc: ResearchService = Depends(service)):
    return svc.issue_receipt(
        project_id,
        body.question,
        body.model,
        body.workflow_version,
        body.report_text,
        body.evidence_bundle,
        body.warnings,
        body.limitations,
    )


@router.get("/projects/{project_id}/receipts", response_model=list[ReceiptRead])
def list_receipts(project_id: int, svc: ResearchService = Depends(service)):
    return svc.list_entities("receipts", project_id)


@router.post(
    "/projects/{project_id}/workflow/execute",
    response_model=WorkflowRead,
    status_code=201,
)
def execute_workflow(
    project_id: int,
    body: WorkflowExecute,
    session: Session = Depends(get_session),
    providers: AIProviderRegistry = Depends(ai_provider_registry),
):
    return ResearchWorkflowService(session, providers.resolve(body.provider)).run(
        project_id=project_id,
        question=body.question,
        source_ids=body.source_ids,
        model=body.model,
        max_output_tokens=body.max_output_tokens,
        workflow_version=body.workflow_version,
        publication_title=body.publication_title,
    )
