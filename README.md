# Research OS

Research OS is a constitutional research workspace built around the lifecycle:

`Question → Evidence → Analysis → Knowledge`

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
