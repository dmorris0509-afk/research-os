import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from research_os.api.app import create_app
from research_os.api.router import research_model
from research_os.db import get_session
from research_os.domain.models import Base
from research_os.domain.services.workflow_models import (
    ClaimDraft,
    EvidenceDraft,
    ResearchDraft,
)


class FakeResearchModel:
    def __init__(self, cited_source_id: int | None = None):
        self.cited_source_id = cited_source_id
        self.calls = []

    def research(self, **kwargs):
        self.calls.append(kwargs)
        source_id = self.cited_source_id or kwargs["sources"][0].id
        return ResearchDraft(
            evidence=[
                EvidenceDraft(
                    source_id=source_id,
                    content="The repository has automated tests.",
                    relevance=0.95,
                )
            ],
            claims=[
                ClaimDraft(
                    evidence_indexes=[0],
                    text="The project uses automated testing.",
                    analysis="The cited source contains a test suite.",
                    verdict="pass",
                    verification_details="Directly supported by the supplied repository content.",
                    confidence=0.94,
                )
            ],
            report_markdown="# Finding\n\nThe project uses automated testing [Evidence 1].",
            limitations=["Only the supplied repository snapshot was evaluated."],
        )


@pytest.fixture
def workflow_client(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'workflow.db'}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)

    def override_session():
        with factory() as session:
            try:
                yield session
                session.commit()
            except Exception:
                session.rollback()
                raise

    fake = FakeResearchModel()
    app = create_app()
    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[research_model] = lambda: fake
    with TestClient(app) as client:
        yield client, app, fake
    engine.dispose()


def test_governed_workflow_persists_complete_lineage(workflow_client):
    client, _app, fake = workflow_client
    project_id = client.post("/api/v1/projects", json={"name": "Repository Audit"}).json()["id"]
    source = client.post(
        f"/api/v1/projects/{project_id}/sources",
        json={
            "kind": "github_readme",
            "location": "https://github.com/example/research-os#readme",
            "metadata": {"content": "Tests live in tests/ and run in CI."},
        },
    ).json()

    response = client.post(
        f"/api/v1/projects/{project_id}/workflow/execute",
        json={
            "question": "Does this repository use automated testing?",
            "source_ids": [source["id"]],
            "publication_title": "Repository Audit",
        },
    )

    assert response.status_code == 201
    assert fake.calls[0]["model"] == "gpt-5.6"
    assert len(client.get(f"/api/v1/projects/{project_id}/evidence").json()) == 1
    assert client.get(f"/api/v1/projects/{project_id}/claims").json()[0]["status"] == "verified"
    assert client.get(f"/api/v1/projects/{project_id}/questions").json()[0]["status"] == "completed"
    receipt = client.get(f"/api/v1/projects/{project_id}/receipts").json()[0]
    assert receipt["execution_id"] == response.json()["execution_id"]
    assert receipt["limitations"]
    event_types = [item["type"] for item in client.get(f"/api/v1/projects/{project_id}/timeline").json()]
    assert event_types[-1] == "CONSTITUTIONAL_EXECUTION_COMPLETED"


def test_ungrounded_model_output_rolls_back_entire_workflow(workflow_client):
    client, app, _fake = workflow_client
    app.dependency_overrides[research_model] = lambda: FakeResearchModel(cited_source_id=999)
    project_id = client.post("/api/v1/projects", json={"name": "Rollback"}).json()["id"]
    source = client.post(
        f"/api/v1/projects/{project_id}/sources",
        json={"kind": "text", "location": "memory://one", "metadata": {"content": "Ground truth."}},
    ).json()

    response = client.post(
        f"/api/v1/projects/{project_id}/workflow/execute",
        json={"question": "What is supported?", "source_ids": [source["id"]], "publication_title": "Result"},
    )

    assert response.status_code == 422
    assert client.get(f"/api/v1/projects/{project_id}/evidence").json() == []
    event_types = [item["type"] for item in client.get(f"/api/v1/projects/{project_id}/timeline").json()]
    assert "CONSTITUTIONAL_EXECUTION_STARTED" not in event_types
