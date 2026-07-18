import time
from typing import Protocol

import httpx
import jwt

from .errors import GitHubAuthenticationError


class GitHubAuthProvider(Protocol):
    def token(self) -> str: ...


class StaticTokenAuth:
    """Fine-grained token fallback for local development only."""

    def __init__(self, token: str):
        if not token:
            raise GitHubAuthenticationError("GITHUB_TOKEN is empty")
        self._token = token

    def token(self) -> str:
        return self._token


class GitHubAppAuth:
    """Exchange a short-lived App JWT for an installation token."""

    def __init__(
        self,
        app_id: str,
        installation_id: str,
        private_key: str,
        *,
        api_url="https://api.github.com",
        transport=None,
    ):
        if not all((app_id, installation_id, private_key)):
            raise GitHubAuthenticationError("GitHub App ID, installation ID, and private key are required")
        self.app_id, self.installation_id, self.private_key = app_id, installation_id, private_key
        self.api_url, self.transport = api_url.rstrip("/"), transport
        self._token: str | None = None
        self._expires_at = 0.0

    def _jwt(self) -> str:
        now = int(time.time())
        return jwt.encode(
            {"iat": now - 60, "exp": now + 540, "iss": self.app_id}, self.private_key, algorithm="RS256"
        )

    def token(self) -> str:
        if self._token and time.time() < self._expires_at - 60:
            return self._token
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self._jwt()}",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        try:
            with httpx.Client(transport=self.transport, timeout=20) as client:
                response = client.post(
                    f"{self.api_url}/app/installations/{self.installation_id}/access_tokens", headers=headers
                )
                response.raise_for_status()
                self._token = response.json()["token"]
        except (httpx.HTTPError, KeyError) as exc:
            raise GitHubAuthenticationError("Could not create a GitHub App installation token") from exc
        self._expires_at = time.time() + 3300
        return self._token
