# GitHub integration

Research OS imports repository metadata, README content, Issues, and Pull Requests through the GitHub REST API.

## Authentication

Use a **GitHub App** for deployed environments. It provides granular permissions, installation-scoped repository access, short-lived tokens, and independent revocation. A fine-grained personal access token is supported only as a local-development fallback.

### GitHub App setup

1. Create a GitHub App in the organization or account that owns the repositories.
2. Grant read-only repository permissions for Metadata, Contents, Issues, and Pull requests.
3. Install the app only on repositories Research OS should access.
4. Generate a private key and keep the PEM outside version control.
5. Configure the hosting environment from `.env.example`.

```text
GITHUB_APP_ID=
GITHUB_INSTALLATION_ID=
GITHUB_PRIVATE_KEY_PATH=/secure/path/research-os.private-key.pem
```

Platforms that inject multiline secrets may use `GITHUB_PRIVATE_KEY` instead.

### Fine-grained local token

Create a token limited to selected repositories with read-only Metadata, Contents, Issues, and Pull requests:

```text
GITHUB_TOKEN=
```

Never commit tokens or private keys.

## Design

- `GitHubAuthProvider` isolates authentication.
- `GitHubClient` owns HTTP, pagination, and error translation.
- `GitHubRepositoryImporter` creates an immutable repository snapshot.
- `GitHubImportSink` is the persistence boundary implemented by the Research OS service layer.

This supports future OAuth, webhooks, Discussions, releases, commit history, or GraphQL batching without changing the page or importer contract.
