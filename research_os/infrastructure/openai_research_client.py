from openai import OpenAI, OpenAIError

from research_os.domain.errors import ExternalServiceError, ValidationError
from research_os.domain.services.ai_provider import AIResearchRequest
from research_os.domain.services.workflow_models import ResearchDraft


class OpenAIResearchClient:
    """Structured-output adapter for the OpenAI Responses API."""

    def __init__(self, client: OpenAI | None = None):
        self.client = client or OpenAI()

    @property
    def provider_id(self) -> str:
        return "openai"

    def generate_research(self, request: AIResearchRequest) -> ResearchDraft:
        source_text = "\n\n".join(
            f"SOURCE_ID={source.id}\nTITLE={source.title or 'Untitled'}\n"
            f"LOCATION={source.location}\nCONTENT:\n{source.content}"
            for source in request.sources
        )
        try:
            response = self.client.responses.parse(
                model=request.model,
                instructions=(
                    "You are the governed analysis engine for Research OS. Use only the supplied sources. "
                    "Every evidence item must cite a supplied SOURCE_ID. Distinguish findings from "
                    "inference, prefer inconclusive verdicts when support is insufficient, disclose "
                    "limitations, and write "
                    "a concise Markdown report that explicitly connects claims to evidence."
                ),
                input=f"RESEARCH QUESTION:\n{request.question}\n\nSOURCES:\n{source_text}",
                text_format=ResearchDraft,
                max_output_tokens=request.max_output_tokens,
            )
        except OpenAIError as exc:
            raise ExternalServiceError("OpenAI research execution failed") from exc
        if response.output_parsed is None:
            raise ValidationError("The research model did not return a usable structured result")
        return response.output_parsed
