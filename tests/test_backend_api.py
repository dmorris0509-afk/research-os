import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from research_os.api.app import create_app
from research_os.db import get_session
from research_os.domain.models import Base


@pytest.fixture
def client(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}", connect_args={"check_same_thread": False})
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

    app = create_app()
    app.dependency_overrides[get_session] = override_session
    test_client = TestClient(app)
    yield test_client
    test_client.close()
    engine.dispose()


def test_complete_research_vertical_slice(client):
    project = client.post("/api/v1/projects", json={"name": "AI Tutor Review"})
    assert project.status_code == 201
    project_id = project.json()["id"]

    source = client.post(
        f"/api/v1/projects/{project_id}/sources",
        json={"kind": "url", "location": "https://example.test/study"},
    ).json()
    evidence = client.post(
        f"/api/v1/projects/{project_id}/evidence",
        json={"source_id": source["id"], "kind": "quote", "content": "Tutoring improved outcomes."},
    ).json()
    claim = client.post(
        f"/api/v1/projects/{project_id}/claims",
        json={"evidence_id": evidence["id"], "text": "AI tutoring may improve outcomes."},
    ).json()
    analysis = client.post(
        f"/api/v1/projects/{project_id}/analyses", json={"claim_id": claim["id"], "method": "comparative"}
    )
    verification = client.post(
        f"/api/v1/projects/{project_id}/verifications", json={"claim_id": claim["id"], "result": "pass"}
    )
    publication = client.post(
        f"/api/v1/projects/{project_id}/publications",
        json={"title": "Review", "report_text": "Evidence-backed report"},
    )
    receipt = client.post(
        f"/api/v1/projects/{project_id}/receipts",
        json={
            "question": "Should schools adopt AI tutors?",
            "model": "gpt-5.6",
            "workflow_version": "0.1.0",
            "report_text": "Evidence-backed report",
        },
    )

    assert (
        analysis.status_code
        == verification.status_code
        == publication.status_code
        == receipt.status_code
        == 201
    )
    assert len(receipt.json()["report_hash"]) == 64
    assert len(client.get(f"/api/v1/projects/{project_id}/timeline").json()) == 8


def test_cross_project_reference_is_rejected(client):
    first = client.post("/api/v1/projects", json={"name": "First"}).json()["id"]
    second = client.post("/api/v1/projects", json={"name": "Second"}).json()["id"]
    source = client.post(
        f"/api/v1/projects/{first}/sources", json={"kind": "url", "location": "https://example.test"}
    ).json()
    response = client.post(
        f"/api/v1/projects/{second}/evidence",
        json={"source_id": source["id"], "kind": "quote", "content": "Cross-tenant evidence"},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "conflict"


def test_missing_project_returns_structured_404(client):
    response = client.get("/api/v1/projects/999")
    assert response.status_code == 404
    assert response.json() == {"error": {"code": "not_found", "message": "Project 999 not found"}}
