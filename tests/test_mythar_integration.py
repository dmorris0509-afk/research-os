import httpx
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from research_os.domain.errors import ExternalServiceError, ValidationError
from research_os.domain.models import Base
from research_os.domain.services import MytharISFSink, ResearchService
from research_os.integrations.mythar import MytharCompilerClient, MytharImporter
from research_os.integrations.mythar.models import MytharISF

ISF = {
    "version": "0.4",
    "root": "ema",
    "canonical": True,
    "class": "proclamation",
    "domain": "speech",
    "intent": "declare",
    "operators": [],
    "arguments": [],
    "context": {"source_language": "mythar", "compiler_version": "v2", "line": 1, "column": 1},
    "metadata": {"confidence": 1.0, "notes": []},
}


def test_compiler_uses_v2_isf_contract():
    def handler(request: httpx.Request):
        assert request.url.path == "/v2/compile"
        assert request.url.params["format"] == "isf"
        assert request.headers["authorization"] == "Bearer secret"
        return httpx.Response(200, json=ISF)

    with MytharCompilerClient(
        "https://mythar.test", token="secret", transport=httpx.MockTransport(handler)
    ) as compiler:
        result = compiler.compile_to_isf("ema")

    assert result.root == "ema"
    assert result.semantic_class == "proclamation"


def test_compiler_rejects_unsupported_isf_version():
    invalid = {**ISF, "version": "0.5"}
    transport = httpx.MockTransport(lambda _request: httpx.Response(200, json=invalid))
    with MytharCompilerClient("https://mythar.test", transport=transport) as compiler:
        with pytest.raises(ExternalServiceError):
            compiler.compile_to_isf("ema")


def test_compiler_maps_invalid_source_to_domain_error():
    transport = httpx.MockTransport(lambda _request: httpx.Response(400, json={"error": "invalid"}))
    with MytharCompilerClient("https://mythar.test", transport=transport) as compiler:
        with pytest.raises(ValidationError):
            compiler.compile_to_isf("not-mythar")


def test_importer_persists_source_and_validated_isf(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'mythar.db'}")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)

    class Compiler:
        def compile_to_isf(self, source: str) -> MytharISF:
            assert source == "ema"
            return MytharISF.model_validate(ISF)

    with factory.begin() as session:
        service = ResearchService(session)
        project = service.create_project("Mythar research")
        source_id, isf = MytharImporter(Compiler(), MytharISFSink(service)).import_source(project.id, "ema")

        sources = service.list_entities("sources", project.id)
        evidence = service.list_entities("evidence", project.id)

    assert sources[0].id == source_id
    assert sources[0].source_metadata["isf"]["class"] == "proclamation"
    assert evidence[0].kind == "mythar_isf"
    assert evidence[0].evidence_metadata["canonical"] is True
    assert isf.version == "0.4"
    engine.dispose()

