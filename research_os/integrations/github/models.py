from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class RepositorySnapshot:
    repository: dict[str, Any]
    readme: str | None
    issues: list[dict[str, Any]] = field(default_factory=list)
    pull_requests: list[dict[str, Any]] = field(default_factory=list)

    @property
    def full_name(self) -> str:
        return str(self.repository["full_name"])
