from research_os.integrations.github.models import RepositorySnapshot

from .research_service import ResearchService


class GitHubSnapshotSink:
    """Persist a GitHub snapshot as one source and evidence records."""

    def __init__(self, service: ResearchService):
        self.service = service

    def save_repository_snapshot(self, project_id: int, snapshot: RepositorySnapshot) -> None:
        source = self.service.create_source(
            project_id,
            "github_repo",
            snapshot.repository["html_url"],
            snapshot.repository.get("full_name"),
            snapshot.repository,
        )
        if snapshot.readme:
            self.service.create_evidence(project_id, source.id, snapshot.readme, "readme")
        for issue in snapshot.issues:
            self.service.create_evidence(
                project_id,
                source.id,
                issue.get("body") or issue["title"],
                "github_issue",
                {"number": issue["number"], "url": issue["html_url"]},
            )
        for pull in snapshot.pull_requests:
            self.service.create_evidence(
                project_id,
                source.id,
                pull.get("body") or pull["title"],
                "github_pull_request",
                {"number": pull["number"], "url": pull["html_url"]},
            )
