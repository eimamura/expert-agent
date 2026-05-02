# docs/phase_plans/phase3_implementation_plan.md

## Role

This document is the implementation plan for Phase 3: HTTP API and run persistence.

Phase 3 starts from the released Phase 2 `v2.0.1` baseline recorded in `docs/baselines/version2_phase2_baseline.md`.

## Status

Phase 3 is not started.

## Objective

Expose the local agent runtime through a FastAPI HTTP service, persist run metadata to a database, and keep the CLI workflow supported alongside HTTP.

Reference: `docs/07_future_scaling.md` § Phase 3.

---

## Scope

### New capabilities

- `POST /runs` — create a run, return `{run_id, status}` immediately
- `GET /runs/{run_id}` — return run status, token usage, cost, and final answer
- `GET /runs/{run_id}/trace` — return the validated trace events for a run
- Run metadata persistence in SQLite (same local DB used for domain data, or a separate `runs.db`)
- Async run execution so HTTP responses are non-blocking
- CLI entry point remains fully functional

### Out of scope (do not implement in Phase 3)

- Write SQL tools of any kind
- LangGraph or workflow orchestration
- Multi-agent orchestration
- Web UI
- Vector search or external knowledge retrieval
- Production database mutation
- Multi-tenant isolation or user auth

---

## Recommended stack

| Area | Choice | Reason |
| --- | --- | --- |
| HTTP framework | FastAPI | Lightweight, async-native, automatic OpenAPI docs |
| Run store | SQLite (`runs.db`) | No new infrastructure; upgrade to Postgres in a later phase |
| Background execution | `asyncio` + `concurrent.futures` | Avoid adding a task queue before it is needed |
| JSONL traces | Keep as-is | Local files remain the trace source of truth in Phase 3 |

---

## DB schema (runs table)

| Column | Type | Notes |
| --- | --- | --- |
| `run_id` | TEXT PK | ULID |
| `parent_run_id` | TEXT | Nullable |
| `question` | TEXT | Redacted before storage |
| `status` | TEXT | `queued`, `running`, `success`, `*_error`, … |
| `created_at` | TEXT | ISO 8601 UTC |
| `finished_at` | TEXT | Nullable |
| `total_input_tokens` | INTEGER | Nullable until finished |
| `total_output_tokens` | INTEGER | Nullable until finished |
| `total_cost_usd` | REAL | Nullable until finished |
| `final_answer` | TEXT | Nullable; redacted before storage |
| `input_hash` | TEXT | |
| `config_snapshot` | TEXT | JSON string |
| `error_type` | TEXT | Nullable |
| `error_message` | TEXT | Nullable |

---

## Completion checklist

- [x] Step 1: Add `fastapi` and `uvicorn` to dependencies.
- [x] Step 2: Create `runtime/run_store.py` — SQLite-backed run persistence (`create_run`, `update_run`, `get_run`).
- [x] Step 3: Create `app/api.py` — FastAPI app with `POST /runs`, `GET /runs/{run_id}`, `GET /runs/{run_id}/trace`.
- [x] Step 4: Wire async execution so `POST /runs` returns immediately and the agent loop runs in the background.
- [x] Step 5: Confirm CLI entry point (`app/main.py`) continues to work unchanged.
- [x] Step 6: Write pytest coverage for run store, API endpoints, and async execution.
- [x] Step 7: Update `docs/CURRENT_STATE.md` and `docs/baselines/README.md`.

---

## Guardrails inherited from Phase 2

- Keep SQL access parser-backed, allowlisted, and read-only.
- Keep redaction before LLM input.
- Keep redaction before trace persistence.
- Keep redaction before run metadata storage (`question`, `final_answer`).
- Keep trace schema version `"1.0"` and `NormalizedError` shape intact.
- Keep provider test doubles as the default test path (no live LLM credentials required).
- Keep default tests independent of live provider credentials and production databases.
- Do not add write SQL tools or unrestricted SQL execution.

---

## Implementation Result

**Status:** Complete
**Released:** v3.0.0 (2026-05-02)

**Implemented files:**

| File | Change |
| --- | --- |
| `runtime/run_store.py` | New — `RunStore` class, SQLite-backed (`create_run`, `update_run`, `get_run`) |
| `app/api.py` | New — FastAPI app with `POST /runs`, `GET /runs/{run_id}`, `GET /runs/{run_id}/trace`, `init()` |
| `pyproject.toml` | Added `fastapi>=0.115.0`, `uvicorn[standard]>=0.30.0`; dev: `httpx>=0.27.0` |
| `tests/test_run_store.py` | New — 11 unit tests for run store |
| `tests/test_api.py` | New — 11 API endpoint tests |

**Deviations from plan:**

- Used a module-level `init()` function instead of FastAPI lifespan initially, making the API easier to test. A `_lifespan` context manager was added afterward that calls `init()` on startup, enabling `uvicorn app.api:app` without a custom entrypoint.
- `input_hash` and `config_snapshot` are stored as empty strings at run creation and updated after `run_agent` completes.
- Trace JSONL field order changed to `timestamp`-first after initial implementation (was `sort_keys=True` alphabetical order).

**Test result at completion:** 103 passed, 0 failed.
