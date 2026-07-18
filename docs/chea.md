# CHEA Ω∞ reference implementation

Status: **implemented reference substrate (Draft 0.1 / Conformance Level 0)**

CHEA Ω∞ sits beneath the Constitutional Agent Runtime. It does not authorize research or reinterpret
intent. It realizes an already-authorized Execution Envelope through a conformant runtime adapter and
returns normalized execution evidence.

> Govern once. Execute anywhere. Verify everywhere.

## Normative artifact chain

```text
CCR authorization → Execution Envelope → Broker Selection Record → CER → Evidence → Stewardship
```

### Execution Envelope

The envelope binds execution to an authorization ID, effective actor, purpose, requested and granted
capabilities, resource limits, data boundaries, constitutional and policy versions, evidence requirements,
and workflow context. Granted capabilities must be a subset of requested capabilities.

### Runtime Adapter Contract

An adapter declares a stable identity, capabilities, isolation level, evidence-fidelity class, security
properties, conformance version, health, and attestation support. Its `execute` operation receives the
immutable envelope plus an implementation payload and returns normalized evidence with an output.

The first adapter wraps the provider-neutral Research OS AI provider boundary. OpenAI is therefore an
adapter implementation, not a dependency of CHEA or the research domain.

### Runtime Broker and BSR

The broker is a policy-constrained dispatcher and execution fiduciary. It:

- filters unhealthy adapters and adapters missing granted capabilities;
- enforces minimum assurance and attestation requirements;
- selects the lowest sufficient assurance class, then lexical adapter identity and version;
- ignores broker hints when they conflict with policy;
- records every candidate, rejection reason, policy constraint, and rationale in the BSR; and
- denies execution when no adapter is conformant.

Selection is deterministic for identical adapter registries, envelopes, and policy packs. Fallback is only
allowed to another fully conformant adapter.

### Constitutional Execution Record

Every dispatched execution returns a CER containing authorization and BSR lineage, the selected runtime,
input and output hashes, execution timestamps, lifecycle events, model/tool/service calls, resource use,
limits, anomalies, interventions, verification results, evidence references, and assurance class.

The implementation enforces these invariants:

1. A CER references its authorizing decision and BSR.
2. CER assurance never exceeds registered adapter evidence fidelity.
3. Capability grants cannot exceed the authorized request.
4. Missing guarantees, adapter exceptions, assurance inflation, and resource overruns produce
   `INDETERMINATE`; output is withheld from the research workflow.
5. No conformant adapter produces `DENIED` before execution.
6. Completed CERs are stored inside the append-only Research Receipt evidence bundle and share its
   execution ID.

## Inspect a CER

Run a workflow, retrieve its receipt ID, then call:

```bash
curl http://localhost:8000/api/v1/projects/1/receipts/1/cer
```

The endpoint's Pydantic response model also publishes the complete CER JSON Schema through FastAPI
OpenAPI at `/docs` and `/openapi.json`.

## Assurance scope

The current AI provider adapter declares `LOCAL_PROCESS` evidence fidelity and CHEA Level 0 conformance.
It does not claim sandbox isolation, deterministic model output, hardware attestation, or cryptographic
signing. Those require additional adapters and evidence—not stronger wording.

