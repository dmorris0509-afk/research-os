# Backend architecture and operations

## Boundaries

```text
FastAPI → Domain service → Unit of work / repositories → SQLAlchemy → SQLite or PostgreSQL
                                  ↓
                         Research event timeline
```

The Streamlit UI remains `app.py`. The API entrypoint is `research_os.api.app:app`.

- **API schemas** validate transport data and never contain persistence logic.
- **Domain services** enforce project ownership, state transitions, and event creation.
- **Repositories** only stage persistence operations; they never commit independently.
- **The request transaction** commits the entity and its audit event together or rolls both back.
- **Constitutional runtime** governs AI workflow admission, not ordinary CRUD.
- **AI provider interface** keeps the domain independent of any vendor SDK or model family.
- **GitHub adapter** converts a repository snapshot into a Source plus Evidence records.

## Data lineage

```text
Project → Research Question
        → Source → Evidence → Claim → Analysis → Verification
        → Publication
        → Research Receipt
```

Every creation operation emits a project-scoped `ResearchEvent`. Cross-project references return a structured `409 conflict` instead of creating corrupt lineage.

Evidence-bearing records are append-oriented. The first API slice deliberately avoids generic mutation endpoints that could rewrite historical evidence in place; corrections should create a new record and preserve lineage. Project deletion remains available for local development and test cleanup.

## Configuration

Settings use the `RESEARCH_OS_` prefix and load from process environment, `.env`, or `.env.local`.

| Variable | Default | Purpose |
| --- | --- | --- |
| `RESEARCH_OS_ENVIRONMENT` | `development` | Controls development-only automatic schema creation. |
| `RESEARCH_OS_DATABASE_URL` | `sqlite:///./research_os.db` | SQLAlchemy database URL; PostgreSQL is supported by configuration. |
| `RESEARCH_OS_WORKSPACE_ROOT` | `workspace` | Root for generated or imported files. |
| `RESEARCH_OS_CORS_ORIGINS` | localhost Streamlit | Explicit allowed browser origins. |
| `RESEARCH_OS_AUTH_REQUIRED` | `false` | Enables external JWT validation. |
| `RESEARCH_OS_JWT_SECRET` | none | Required with auth; minimum 32 characters. |
| `OPENAI_API_KEY` | none | OpenAI SDK credential for governed workflow execution. |

No default production credential or fake user store is included. Production identity can later be delegated to an OIDC provider while retaining the `current_principal` dependency.

## Governed workflow

The high-level endpoint resolves a configured provider adapter, runs one typed synthesis, and persists all
derived records in the API request transaction. OpenAI with GPT-5.6 is the current hackathon default, not a
domain dependency:

```http
POST /api/v1/projects/1/workflow/execute
Content-Type: application/json

{
  "question": "What does the supplied evidence support?",
  "source_ids": [1, 2],
  "provider": "openai",
  "model": "gpt-5.6",
  "max_output_tokens": 8000,
  "workflow_version": "1.0.0",
  "publication_title": "Evidence Review"
}
```

Only source IDs owned by the project are accepted. Each source must contain captured text in
`source_metadata.content`. Model-produced evidence citing any other source is rejected, and the request
transaction rolls back. The resulting receipt records entity IDs, disclosed limitations, the execution ID,
workflow/model versions, and a SHA-256 report hash. It is tamper-evident, not cryptographically signed;
signature support is intentionally deferred until a managed signing-key design exists.

The timeline is a chronological reconstruction of persisted actions. Deterministic replay is not claimed:
that would additionally require immutable model snapshots, prompt versions, sampling parameters, and full
input capture.

Provider implementations satisfy the `AIProvider` protocol and receive an `AIResearchRequest`. Core
services consume the provider-neutral `ResearchDraft`; only infrastructure adapters import vendor SDKs.
`AIProviderRegistry` rejects unknown providers with a structured domain validation error. Adding another
provider therefore requires an adapter plus governance configuration, not changes to the workflow service.

## Database lifecycle

Local development may initialize tables automatically. Shared or deployed environments must run:

```bash
alembic upgrade head
```

The initial migration is reversible and verified in CI-compatible tests.

## Quality gates

```bash
ruff check research_os tests migrations
pytest --cov=research_os --cov-report=term-missing --cov-fail-under=70
alembic upgrade head
alembic downgrade base
```
