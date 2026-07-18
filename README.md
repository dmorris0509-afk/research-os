# Research OS

Research OS is a constitutional research workspace built around the lifecycle:

`Question → Evidence → Analysis → Knowledge`

It turns supplied source material into inspectable evidence, claims, analysis, verification, a Markdown
publication, and a SHA-256-backed execution receipt. GPT-5.6 performs structured synthesis; Research OS
enforces source boundaries and persists the resulting lineage atomically.

## GitHub integration

Research OS can connect a repository and import repository metadata, README content, Issues, and Pull Requests as structured research inputs. Deployed environments use a granular GitHub App installation; local development can use a repository-scoped fine-grained token.

See [GitHub integration setup](docs/github-integration.md).

## Run locally

```bash
python -m venv .venv
pip install -r requirements.txt
streamlit run app.py
```

Run the automated tests with `pytest -q`.

## Backend API

The production-facing API is separate from the Streamlit entrypoint:

```bash
uvicorn research_os.api.app:app --reload
```

- OpenAPI: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`
- Versioned API: `http://localhost:8000/api/v1`

Apply database migrations with `alembic upgrade head`.

### Run a governed research workflow

1. Create a project with `POST /api/v1/projects`.
2. Add one or more sources with `POST /api/v1/projects/{id}/sources`. Each workflow source must include
   its captured text in `metadata.content`.
3. Call `POST /api/v1/projects/{id}/workflow/execute` with the source IDs and research question.
4. Inspect `/timeline`, `/evidence`, `/claims`, `/publications`, and `/receipts`.

The endpoint uses `OPENAI_API_KEY` from the process environment. Real credentials are never stored in the
repository. See [Backend architecture and operations](docs/backend.md) for an example request.

## Built with Codex and GPT-5.6

Codex converted the initial Streamlit proof of concept and architecture briefs into the layered API,
transactional lineage model, migrations, GitHub integration, adversarial provenance tests, and CI checks.
GPT-5.6 is the governed research engine at runtime through the OpenAI Responses API with typed structured
outputs. See the [Codex build log](BUILD_LOG.md) for key implementation decisions.

## License

Copyright 2026 `dmorris0509-afk`. Licensed under the MIT License.
