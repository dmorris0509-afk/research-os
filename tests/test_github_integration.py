import httpx
import pytest

from research_os.integrations.github.auth import GitHubAppAuth, StaticTokenAuth
from research_os.integrations.github.client import GitHubClient
from research_os.integrations.github.errors import GitHubAuthenticationError, GitHubNotFoundError
from research_os.integrations.github.importer import GitHubRepositoryImporter


def github_transport(request: httpx.Request) -> httpx.Response:
    path = request.url.path
    if path == "/repos/acme/research":
        return httpx.Response(200, json={"full_name": "acme/research", "stargazers_count": 7})
    if path == "/repos/acme/research/readme":
        return httpx.Response(200, text="# Research")
    if path == "/repos/acme/research/issues":
        return httpx.Response(
            200,
            json=[
                {"number": 1, "title": "Issue", "html_url": "https://example.test/i/1"},
                {"number": 2, "title": "PR", "pull_request": {}, "html_url": "https://example.test/p/2"},
            ],
        )
    if path == "/repos/acme/research/pulls":
        return httpx.Response(
            200, json=[{"number": 2, "title": "Improve", "html_url": "https://example.test/p/2"}]
        )
    return httpx.Response(404, json={"message": "Not Found"})


def make_importer(transport=github_transport):
    client = GitHubClient(StaticTokenAuth("test-token"), transport=httpx.MockTransport(transport))
    return GitHubRepositoryImporter(client)


def test_import_repository_snapshot():
    snapshot = make_importer().import_repository("acme/research")
    assert snapshot.full_name == "acme/research"
    assert snapshot.readme == "# Research"
    assert [issue["number"] for issue in snapshot.issues] == [1]
    assert [pull["number"] for pull in snapshot.pull_requests] == [2]


@pytest.mark.parametrize("value", ["", "owner", "owner/repo/extra", "/repo"])
def test_repository_name_validation(value):
    with pytest.raises(ValueError):
        GitHubRepositoryImporter.validate_full_name(value)


def test_authentication_error_is_actionable():
    with pytest.raises(GitHubAuthenticationError):
        make_importer(lambda request: httpx.Response(401)).import_repository("acme/research")


def test_not_found_is_actionable():
    with pytest.raises(GitHubNotFoundError):
        make_importer(lambda request: httpx.Response(404)).import_repository("acme/research")


def test_github_app_exchanges_for_installation_token(monkeypatch):
    monkeypatch.setattr("research_os.integrations.github.auth.jwt.encode", lambda *args, **kwargs: "app-jwt")

    def transport(request):
        assert request.url.path == "/app/installations/42/access_tokens"
        assert request.headers["authorization"] == "Bearer app-jwt"
        return httpx.Response(201, json={"token": "installation-token"})

    auth = GitHubAppAuth(
        "7",
        "42",
        "private-key",
        transport=httpx.MockTransport(transport),
    )
    assert auth.token() == "installation-token"
    assert auth.token() == "installation-token"
