# Research OS

Research OS is a constitutional research workspace built around the lifecycle:

`Question → Evidence → Analysis → Knowledge`

It turns supplied source material into inspectable evidence, claims, analysis, verification, a Markdown
publication, and a SHA-256-backed execution receipt. A provider-neutral AI boundary performs structured
synthesis; the hackathon configuration uses OpenAI GPT-5.6. Research OS enforces source boundaries and
persists the resulting lineage atomically.

## GitHub integration

Research OS can connect a repository and import repository metadata, README content, Issues, and Pull Requests as structured research inputs. Deployed environments use a granular GitHub App installation; local development can use a repository-scoped fine-grained token.

See [GitHub integration setup](docs/github-integration.md).

## Mythar integration

Research OS accepts Mythar source through a modular compiler client, validates the resulting Mythar ISF
v0.4 semantic artifact, and preserves both the source and ISF in the evidence lineage. See
[Mythar integration setup](docs/mythar-integration.md).

## Quick Start

### Installation

Research OS requires Python 3.11 or newer.

```bash
python -m venv .venv
```

Activate the environment (`.venv\\Scripts\\activate` on Windows or `source .venv/bin/activate` on
macOS/Linux), then install the dependencies:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Running locally

```bash
streamlit run app.py
```

Open `http://localhost:8501`. The judge demo loads a clearly labeled verified sample workspace and does
not require credentials. An `OPENAI_API_KEY` is only needed to execute live AI workflows; copy
`.env.example` and provide credentials through your environment rather than committing secrets.

### Feature overview

- Evidence-first research dashboard with projects, questions, sources, claims, and publications.
- Inspectable provenance, verification state, execution timeline, and SHA-256-backed receipts.
- Provider-neutral AI interface with an OpenAI Responses API adapter for the hackathon runtime.
- GitHub repository import for metadata, README content, Issues, and Pull Requests.
- Mythar compiler integration with strict ISF v0.4 validation and evidence-lineage persistence.
- FastAPI backend with SQLite persistence, migrations, OpenAPI documentation, tests, and CI.

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
The domain workflow is model-agnostic and selects adapters through an AI provider registry. The hackathon
runtime registers OpenAI's Responses API adapter and uses GPT-5.6 typed structured outputs by default. See
the [Codex build log](BUILD_LOG.md) for key implementation decisions.

## License

Copyright 2026 `dmorris0509-afk`. Licensed under the MIT License.
