# docs/07_future_scaling.md

## Role

This document defines the direction for Phase 3 and later: Web/API, external search, LangGraph, channels, and agent platform evolution.

## Read first

- `../SPEC.md`
- `docs/00_project_overview.md`
- `docs/01_architecture_principles.md`

## Related documents

- `docs/02_phase1_mvp_scope.md`

## Implementation target

- Do not implement this work in Phase 1.
- Revisit this document when planning later phases.

---

# Future Scaling

## Phase 3: Web/API

### Goal

Expose the local agent runtime through a service boundary once the CLI behavior is proven.

### Recommended stack

- FastAPI for the HTTP API.
- SQLite or Postgres for run metadata.
- JSONL trace files can remain initially.
- Background workers only when needed.

### Candidate API

```http
POST /runs
GET /runs/{run_id}
GET /runs/{run_id}/trace
```

### `POST /runs`

Input:

```json
{
  "question": "Explain the monthly revenue change.",
  "config_overrides": {}
}
```

Output:

```json
{
  "run_id": "01H...",
  "status": "queued"
}
```

### DB persistence candidates

- run id;
- parent run id;
- question;
- status;
- timestamps;
- token usage;
- cost;
- final answer;
- input hash;
- config snapshot.

### Phase 3 completion criteria

- Runs can be created through HTTP.
- Run status can be retrieved.
- Trace can be retrieved.
- CLI behavior remains supported.
- No write SQL tools are introduced by default.

## Phase 4: External search

### Goal

Move beyond naive Markdown file listing when the knowledge base becomes too large.

### Triggers

Consider external search when:

- Markdown files are too numerous for the prompt index;
- retrieval quality becomes poor;
- latency becomes unacceptable;
- multiple knowledge domains need isolation.

### Candidate technologies

- SQLite FTS for local search.
- Postgres full-text search.
- Vector DB only when semantic retrieval is needed.
- Hybrid search if keyword and semantic search are both needed.

### Migration policy

The search layer should remain behind an interface so the agent loop does not depend on a specific retrieval backend.

## Phase 5: LangGraph / workflow orchestration

### Goal

Introduce explicit workflow orchestration after the minimal loop behavior is proven.

### Triggers

Consider LangGraph when:

- the loop has several stable branches;
- retries and state transitions become complex;
- multiple tools need structured routing;
- parent/child runs become important;
- human approval steps are needed.

### Migration policy

Keep Phase 1 loop semantics as the reference behavior. LangGraph should preserve:

- redaction before LLM input;
- redaction before trace persistence;
- max step, token, and cost limits;
- trace event schema compatibility;
- input hash semantics.

## Phase 6: Multiple channels

### Goal

Expose the agent through more than one user channel.

Candidate channels:

- CLI;
- Web UI;
- Slack;
- scheduled reports;
- internal tools.

### Policy

Channels should be adapters around the same runtime. Do not duplicate core agent logic per channel.

## Phase 7: Agent platform

### Goal

Turn the project into a reusable internal agent platform only after the domain agent proves value.

Potential platform features:

- multiple domain agents;
- shared tool registry;
- shared policy registry;
- centralized trace storage;
- approval workflows;
- user and tenant isolation;
- evaluation dashboards;
- cost controls;
- model routing.

## Final direction

Start with:

```text
Markdown-centered knowledge
single agent
custom minimal loop
read-only tools
SQL safety
redaction
trace
eval
CLI
```

Then expand only when the operational need is clear:

```text
Web/API
external search
LangGraph / workflow
channel integrations
agent platform
```

