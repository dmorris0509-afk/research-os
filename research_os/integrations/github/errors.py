class GitHubIntegrationError(RuntimeError):
    """Base error for actionable GitHub integration failures."""


class GitHubAuthenticationError(GitHubIntegrationError):
    pass


class GitHubNotFoundError(GitHubIntegrationError):
    pass
