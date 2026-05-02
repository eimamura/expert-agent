# docs/baselines/version3_phase3_baseline.md

## Purpose

Version 3 records the completed Phase 3: HTTP API exposure and SQLite-backed run persistence added on top of the Phase 2 runtime.

Phase 3 exists to make the agent accessible beyond the local CLI — any HTTP client can create runs, poll their status, and retrieve trace events. It is a comparison baseline for Phase 4.

## Implemented Capabilities

All Phase 1 and Phase 2 capabilities are preserved. Phase 3 adds:

- FastAPI HTTP application in `app/api.py` — schema version `3.0.0`.
- `POST /runs` — create a run, return `{run_id, status: "queued"}` with HTTP 202. The agent loop executes asynchronously in a background thread.
- `GET /runs/{run_id}` — return run metadata (status, token usage, cost, final answer, error info). `config_snapshot` is excluded from the response.
- `GET /runs/{run_id}/trace` — load and validate the JSONL trace for a run, return events as JSON.
- `runtime/run_store.py` — `RunStore` class backed by SQLite (`runs.db`). Operations: `create_run`, `update_run`, `get_run`.
- Run lifecycle: `queued` → `running` → terminal status (mirrors `run_finished` statuses from Phase 2).
- Redaction before DB storage: `question` and `final_answer` are passed through `redact_text()` before being written to `runs.db`.
- `app/api.init()` — explicit initialization function (config load + RunStore creation). Also wired to a FastAPI `lifespan` so `uvicorn app.api:app` calls `init()` automatically on startup.
- Background execution via `asyncio.get_running_loop().run_in_executor()` — the blocking `run_agent` call runs in a thread pool and does not block the event loop.
- HTTP 503 returned when the service is not initialized (guards against calls before `init()` is invoked).
- Trace JSONL events write `timestamp` as the first field, followed by remaining fields in insertion order.
- HTTP 404 for unknown run IDs or missing trace files.

## Run Store Schema

| Column | Type | Notes |
| --- | --- | --- |
| `run_id` | TEXT PK | ULID |
| `parent_run_id` | TEXT | Nullable |
| `question` | TEXT | Redacted before storage |
| `status` | TEXT | `queued`, `running`, or any `run_finished` terminal status |
| `created_at` | TEXT | ISO 8601 UTC |
| `finished_at` | TEXT | Nullable until run completes |
| `total_input_tokens` | INTEGER | Nullable until run completes |
| `total_output_tokens` | INTEGER | Nullable until run completes |
| `total_cost_usd` | REAL | Nullable until run completes |
| `final_answer` | TEXT | Nullable; redacted before storage |
| `input_hash` | TEXT | Updated after run_agent completes |
| `config_snapshot` | TEXT | JSON string; updated after run_agent completes |
| `error_type` | TEXT | Nullable |
| `error_message` | TEXT | Nullable |

## Safety and Guardrails

All Phase 1 and Phase 2 guardrails are preserved. Phase 3 adds:

- `question` and `final_answer` are redacted before storage in `runs.db`.
- The HTTP API does not expose raw `config_snapshot` in `GET /runs/{run_id}` responses.
- No write SQL tools were introduced.
- No new production mutation paths were introduced.
- The CLI entrypoint (`app/main.py`) is unchanged.

## Known Limitations

All Phase 2 limitations carried forward. Phase 3 additions:

- `runs.db` is a local SQLite file; there is no replication, backup, or migration tooling.
- Concurrent writes to `runs.db` rely on SQLite's built-in serialization (`check_same_thread=False`). Not suitable for multi-process deployments without a Postgres upgrade.
- There is no authentication or authorization on the HTTP API.
- There is no rate limiting on HTTP endpoints.
- `POST /runs` does not support `config_overrides` yet (the field is accepted but ignored).
- Background tasks run in the default `ThreadPoolExecutor`; there is no queue or retry mechanism.
- The API must be started manually with `uvicorn app.api:app` after calling `app.api.init()`.

## Version 3 Baseline for Phase 4 Comparison

Phase 4 should preserve:

- All Phase 2 trace and eval guardrails.
- Run store schema and `RunStore` interface.
- Redaction before DB storage of `question` and `final_answer`.
- `POST /runs` → `GET /runs/{id}` → `GET /runs/{id}/trace` API contract.
- HTTP 202 for accepted runs, 404 for missing resources, 503 for uninitialized service.
- CLI behavior via `app/main.py`.
- No write SQL tools or unrestricted SQL.

Phase 4 may improve:

- Knowledge retrieval quality (SQLite FTS, Postgres full-text, or vector search).
- Run store migration to Postgres for multi-process deployments.
- Authentication on the HTTP API.
- `config_overrides` support in `POST /runs`.

Phase 4 may replace later:

- SQLite `runs.db` with a Postgres-backed run store.
- The naive Markdown listing strategy with an indexed retrieval layer.
