import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GitHubSettings:
    api_url: str = os.getenv("GITHUB_API_URL", "https://api.github.com")
    api_version: str = os.getenv("GITHUB_API_VERSION", "2022-11-28")
    app_id: str | None = os.getenv("GITHUB_APP_ID")
    installation_id: str | None = os.getenv("GITHUB_INSTALLATION_ID")
    private_key: str | None = os.getenv("GITHUB_PRIVATE_KEY")
    private_key_path: str | None = os.getenv("GITHUB_PRIVATE_KEY_PATH")
    token: str | None = os.getenv("GITHUB_TOKEN")

    def resolved_private_key(self) -> str | None:
        if self.private_key:
            return self.private_key.replace("\\n", "\n")
        if self.private_key_path:
            return Path(self.private_key_path).read_text(encoding="utf-8")
        return None
