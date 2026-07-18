import json

from research_os.integrations.mythar.models import MytharISF

from .research_service import ResearchService


class MytharISFSink:
    """Persist source text and validated ISF without coupling research services to Mythar."""

    def __init__(self, service: ResearchService):
        self.service = service

    def save_mythar_artifact(self, project_id: int, source_text: str, isf: MytharISF) -> int:
        payload = isf.model_dump(mode="json", by_alias=True)
        source = self.service.create_source(
            project_id,
            "mythar",
            f"mythar://isf/{isf.version}/{isf.root}",
            f"Mythar: {isf.root}",
            {"source_text": source_text, "isf": payload},
        )
        self.service.create_evidence(
            project_id,
            source.id,
            json.dumps(payload, ensure_ascii=False, sort_keys=True),
            "mythar_isf",
            {
                "isf_version": isf.version,
                "canonical": isf.canonical,
                "root": isf.root,
                "compiler_version": isf.context.compiler_version,
            },
        )
        return source.id

