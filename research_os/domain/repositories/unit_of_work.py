from sqlalchemy.orm import Session

from research_os.domain.models import (
    Analysis,
    Claim,
    Evidence,
    Project,
    Publication,
    ResearchEvent,
    ResearchQuestion,
    ResearchReceipt,
    Source,
    Verification,
)

from .base import Repository


class UnitOfWork:
    """Repository registry sharing one transaction-scoped session."""

    def __init__(self, session: Session):
        self.session = session
        self.projects = Repository(session, Project)
        self.questions = Repository(session, ResearchQuestion)
        self.sources = Repository(session, Source)
        self.evidence = Repository(session, Evidence)
        self.claims = Repository(session, Claim)
        self.analyses = Repository(session, Analysis)
        self.verifications = Repository(session, Verification)
        self.publications = Repository(session, Publication)
        self.events = Repository(session, ResearchEvent)
        self.receipts = Repository(session, ResearchReceipt)
