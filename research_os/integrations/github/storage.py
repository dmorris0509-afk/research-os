from typing import Protocol

from .models import RepositorySnapshot


class GitHubImportSink(Protocol):
    """Implemented by the Research OS service layer after its models are pushed."""

    def save_repository_snapshot(self, project_id: int, snapshot: RepositorySnapshot) -> None: ...


class GitHubImportService:
    def __init__(self, importer, sink: GitHubImportSink):
        self.importer, self.sink = importer, sink

    def connect(self, project_id: int, full_name: str) -> RepositorySnapshot:
        snapshot = self.importer.import_repository(full_name)
        self.sink.save_repository_snapshot(project_id, snapshot)
        return snapshot
