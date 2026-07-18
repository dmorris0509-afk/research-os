# Codex build log

## OpenAI Build Week extension

Codex was used to turn the initial Streamlit shell and supplied architecture briefs into an executable backend foundation.

Codex accelerated:

- consolidation of six overlapping backend proposals;
- SQLAlchemy 2 and Pydantic 2 modernization;
- project-scoped lineage and transactional event design;
- FastAPI transport schemas and structured error handling;
- Alembic migration generation;
- vertical-slice, security, and governance tests; and
- GitHub Actions quality gates.
- a single structured GPT-5.6 Responses API boundary instead of multiple opaque model calls;
- source allow-list enforcement and transaction rollback for ungrounded output; and
- chronological lineage with hash-backed (not falsely described as signed) receipts.

Human product decisions retained in the implementation include the Research OS lifecycle, constitutional workflow boundary, evidence-first lineage, Research Receipts, and GitHub as a research source.

The backend work is isolated in dated Git commits so judges can distinguish it from pre-hackathon code.

## Key decisions

- One model call per workflow keeps the demo responsive and creates one auditable structured result.
- Model output may transform supplied evidence but cannot introduce a new source identifier.
- Services and repositories never commit independently; the API request is the transaction boundary.
- Tests use a deterministic model double, so CI never requires or spends an API key.
