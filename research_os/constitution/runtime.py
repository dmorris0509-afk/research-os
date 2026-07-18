from dataclasses import dataclass

from research_os.domain.errors import ValidationError


@dataclass(frozen=True)
class WorkflowRequest:
    project_id: int
    question: str
    model: str
    max_output_tokens: int


@dataclass(frozen=True)
class WorkflowConstraints:
    allowed_models: tuple[str, ...] = ("gpt-5.6",)
    max_output_tokens: int = 20_000
    require_sources: bool = True
    require_limitations: bool = True


class ConstitutionalRuntime:
    """Validate workflow intent without assuming authority over CRUD."""

    def __init__(self, constraints: WorkflowConstraints | None = None):
        self.constraints = constraints or WorkflowConstraints()

    def authorize(self, request: WorkflowRequest) -> WorkflowRequest:
        if not request.question.strip():
            raise ValidationError("Research question is required")
        if request.model not in self.constraints.allowed_models:
            raise ValidationError(f"Model {request.model!r} is not allowed")
        if not 1 <= request.max_output_tokens <= self.constraints.max_output_tokens:
            raise ValidationError("Requested output token budget exceeds the constitutional limit")
        return request
