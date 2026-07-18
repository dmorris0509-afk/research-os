from .auth import GitHubAppAuth, StaticTokenAuth
from .client import GitHubClient
from .config import GitHubSettings
from .errors import GitHubAuthenticationError


def create_github_client(settings: GitHubSettings | None = None) -> GitHubClient:
    settings = settings or GitHubSettings()
    private_key = settings.resolved_private_key()
    if settings.app_id and settings.installation_id and private_key:
        auth = GitHubAppAuth(settings.app_id, settings.installation_id, private_key, api_url=settings.api_url)
    elif settings.token:
        auth = StaticTokenAuth(settings.token)
    else:
        raise GitHubAuthenticationError("Configure a GitHub App installation or a fine-grained GITHUB_TOKEN")
    return GitHubClient(auth, api_url=settings.api_url, api_version=settings.api_version)
