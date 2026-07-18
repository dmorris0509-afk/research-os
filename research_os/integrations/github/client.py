from collections.abc import Iterator
from typing import Any

import httpx

from .auth import GitHubAuthProvider
from .errors import GitHubAuthenticationError, GitHubIntegrationError, GitHubNotFoundError


class GitHubClient:
    def __init__(self, auth: GitHubAuthProvider, *, api_url="https://api.github.com", api_version="2022-11-28", transport=None):
        self.auth, self.api_url, self.api_version, self.transport = auth, api_url.rstrip("/"), api_version, transport

    def _headers(self, accept: str) -> dict[str, str]:
        return {"Accept": accept, "Authorization": f"Bearer {self.auth.token()}", "X-GitHub-Api-Version": self.api_version, "User-Agent": "research-os"}

    def get(self, path: str, *, params: dict[str, Any] | None = None, accept="application/vnd.github+json") -> httpx.Response:
        try:
            with httpx.Client(transport=self.transport, timeout=30, follow_redirects=True) as client:
                response = client.get(f"{self.api_url}{path}", params=params, headers=self._headers(accept))
        except httpx.HTTPError as exc:
            raise GitHubIntegrationError("GitHub request failed before a response was received") from exc
        if response.status_code == 401:
            raise GitHubAuthenticationError("GitHub rejected the configured credentials")
        if response.status_code == 404:
            raise GitHubNotFoundError("Repository not found, or the installation lacks access")
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise GitHubIntegrationError(f"GitHub returned HTTP {response.status_code}") from exc
        return response

    def paginate(self, path: str, *, params: dict[str, Any] | None = None) -> Iterator[dict[str, Any]]:
        page = 1
        while True:
            items = self.get(path, params={**(params or {}), "per_page": 100, "page": page}).json()
            if not isinstance(items, list):
                raise GitHubIntegrationError("Expected a list response from GitHub")
            yield from items
            if len(items) < 100:
                break
            page += 1
