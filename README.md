# expert-agent

Local-first domain expert AI agent MVP.

This repository implements a local-first, single-agent, Markdown-centered expert assistant. It runs from a local CLI or a FastAPI HTTP service, loads curated Markdown knowledge, uses parser-validated read-only SQL tools, redacts sensitive data before LLM input and trace persistence, and writes JSONL traces for each run.

## Project Status

| Phase | Status | Baseline |
| --- | --- | --- |
| Phase 1 — CLI MVP | Complete | `docs/baselines/version1_phase1_baseline.md` |
| Phase 2 — Trace, eval, runtime refinement | Complete | `docs/baselines/version2_phase2_baseline.md` |
| Phase 3 — HTTP API and run persistence | Complete | `docs/baselines/version3_phase3_baseline.md` |

The current scope intentionally excludes Web UI, LangGraph, multi-agent orchestration, vector search, write SQL tools, unrestricted SQL execution, and production mutations.

## Requirements

- Python 3.10+
- `uv`
- `sqlite3` CLI for inspecting the optional local SQLite database
- Anthropic API key for real agent runs
- Optional local database configured through `DATABASE_URL`

Install dependencies:

```bash
uv sync
```

Create local environment values:

```bash
cp .env.example .env
```

Set `ANTHROPIC_API_KEY` in `.env` before running.

Create the optional local SQLite seed database:

```bash
uv run python scripts/create_local_sqlite.py
```

This creates `data/local.sqlite`, matching `DATABASE_URL=sqlite:///./data/local.sqlite` in `.env.example`.

## CLI Usage

Run the local expert agent:

```bash
uv run python -m app.main "What should I investigate first?"
```

Run deterministic local eval validation:

```bash
uv run python app/main.py eval
```

Summarize a JSONL trace:

```bash
uv run python app/main.py trace-summary fixtures/traces/success_basic.jsonl
```

## HTTP API Usage

Initialize and start the API server:

```python
import app.api as api
import uvicorn

api.init()  # loads config and creates RunStore (runs.db)
uvicorn.run(api.app, host="0.0.0.0", port=8000)
```

### Endpoints

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/runs` | Create a run. Returns `{run_id, status}` with HTTP 202. Agent executes in the background. |
| `GET` | `/runs/{run_id}` | Run status, token usage, cost, and final answer. |
| `GET` | `/runs/{run_id}/trace` | Validated JSONL trace events as JSON. |

Example:

```bash
curl -X POST http://localhost:8000/runs \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the current MRR?"}'

# {"run_id": "01J...", "status": "queued"}

curl http://localhost:8000/runs/01J...
curl http://localhost:8000/runs/01J.../trace
```

## Test

```bash
uv run pytest
```

The tests cover config validation, knowledge loading, redaction, SQL safety, SQL wrappers, runtime loop behavior with provider doubles, trace writing, trace schema validation, trace replay, trace summaries, eval assertions, response formatting, run store operations, and HTTP API endpoints.

## Repository Layout

```text
agents/     Prompt contract and agent-facing instructions
app/        CLI entry point (main.py) and HTTP API (api.py)
config/     Runtime configuration
domains/    Domain packs with knowledge, skills, policies, rules, and evals
docs/       Detailed project specification by topic
  baselines/    Versioned completion snapshots
  decisions/    Architecture Decision Records (ADRs)
  phase_plans/  Phase planning records and completion summaries
  reviews/      Review records
runtime/    Agent loop, state, config, tracing, hashing, cost, redaction, run store
scripts/    Local developer setup utilities
tests/      Pytest suite
tools/      Read-only tool implementations
traces/     Per-run JSONL trace output
fixtures/   Redacted trace fixtures for schema, replay, and summary tests
```

## Read Order

Before making implementation changes:

1. `docs/CURRENT_STATE.md` — current phase, routing, and active exclusions
2. `SPEC.md`
3. `docs/00_project_overview.md` and `docs/01_architecture_principles.md`
4. `docs/baselines/README.md` and `docs/phase_plans/README.md`
5. `docs/decisions/ADR-*.md` for the relevant architectural constraint
6. Topic-specific `docs/*.md` for the area being changed

## Safety Notes

- Use read-only database credentials.
- Only parser-validated single-statement `SELECT` queries are allowed.
- Keep redaction before LLM input and before trace persistence.
- Redact `question` and `final_answer` before storing in `runs.db`.
- Do not add write SQL tools or an unrestricted SQL execution function.
- Keep the runtime single-agent unless a later phase explicitly changes it.
