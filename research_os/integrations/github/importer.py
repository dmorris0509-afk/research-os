from .client import GitHubClient
from .models import RepositorySnapshot


class GitHubRepositoryImporter:
    def __init__(self, client: GitHubClient):
        self.client = client

    @staticmethod
    def validate_full_name(full_name: str) -> tuple[str, str]:
        parts = full_name.strip().split("/")
        if len(parts) != 2 or not all(parts):
            raise ValueError("Repository must use owner/name format")
        return parts[0], parts[1]

    def import_repository(self, full_name: str) -> RepositorySnapshot:
        owner, name = self.validate_full_name(full_name)
        base = f"/repos/{owner}/{name}"
        repository = self.client.get(base).json()
        readme = self.client.get(f"{base}/readme", accept="application/vnd.github.raw+json").text or None
        all_issues = list(self.client.paginate(f"{base}/issues", params={"state": "all"}))
        issues = [item for item in all_issues if "pull_request" not in item]
        pulls = list(self.client.paginate(f"{base}/pulls", params={"state": "all"}))
        return RepositorySnapshot(repository, readme, issues, pulls)
