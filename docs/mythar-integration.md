# Mythar integration

Research OS integrates Mythar through the versioned Intermediate Semantic Form (ISF), not through
compiler internals. This keeps the research domain independent from Mythar while preserving semantic
artifacts as inspectable evidence.

## Configuration

```env
RESEARCH_OS_MYTHAR_BASE_URL=https://your-mythar-compiler.example
RESEARCH_OS_MYTHAR_API_TOKEN=replace-with-a-secret-from-your-secret-manager
RESEARCH_OS_MYTHAR_TIMEOUT_SECONDS=15
```

The API token is optional when the compiler does not require authentication. Never commit a real token.

## Import a Mythar artifact

```bash
curl -X POST http://localhost:8000/api/v1/projects/1/mythar/import \
  -H "Content-Type: application/json" \
  -d '{"source":"ema"}'
```

Research OS calls `POST /v2/compile?format=isf`, validates the response against ISF v0.4, then writes:

- one `mythar` source containing the original expression and validated ISF;
- one `mythar_isf` evidence record containing the canonical semantic representation; and
- normal `SOURCE_INGESTED` and `EVIDENCE_EXTRACTED` lineage events.

Unsupported ISF versions and malformed compiler responses are rejected before persistence. Compiler
credentials remain isolated in the infrastructure boundary.

