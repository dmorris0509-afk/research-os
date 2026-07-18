from dataclasses import dataclass
from typing import Protocol

from research_os.domain.errors import ValidationError

from .workflow_models import ResearchDraft, ResearchSource


@dataclass(frozen=True)
class AIResearchRequest:
    question: str
    sources: list[ResearchSource]
    model: str
    max_output_tokens: int


class AIProvider(Protocol):
    """Provider-neutral boundary used by the research domain."""

    @property
    def provider_id(self) -> str: ...

    def generate_research(self, request: AIResearchRequest) -> ResearchDraft: ...


class AIProviderRegistry:
    def __init__(self, providers: list[AIProvider]):
        self._providers = {provider.provider_id: provider for provider in providers}
        if len(self._providers) != len(providers):
            raise ValueError("AI provider IDs must be unique")

    def resolve(self, provider_id: str) -> AIProvider:
        try:
            return self._providers[provider_id]
        except KeyError as exc:
            raise ValidationError(f"AI provider {provider_id!r} is not configured") from exc
