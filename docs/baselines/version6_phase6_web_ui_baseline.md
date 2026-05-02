# docs/baselines/version6_phase6_web_ui_baseline.md

## Role

This is the Phase 6 Web UI completion baseline. It records the stable state for
the Web UI channel adapter added after Phase 4. Phase 5 was intentionally
skipped by ADR-0005 because LangGraph trigger conditions were not met.

## What was delivered

Phase 6 added a minimal browser-based channel adapter over the existing FastAPI
run API.

### New files

| File | Purpose |
| --- | --- |
| `app/static/index.html` | Vanilla HTML/JS single-page UI for asking questions, polling run status, rendering Markdown answers, and showing token/cost metadata. |
| `docs/baselines/version6_phase6_web_ui_baseline.md` | This completion baseline. |

### Modified files

| File | Change |
| --- | --- |
| `app/api.py` | Added `GET /` to serve `app/static/index.html` with `FileResponse`; API version is `6.0.0`. |
| `tests/test_api.py` | Added coverage for `GET /` returning static HTML content while preserving existing `/runs` initialization behavior tests. |
| `README.md` | Documented Web UI usage, the `GET /` endpoint, and Phase 6 status. |
| `SPEC.md` | Updated current baseline and out-of-scope items after Web UI completion. |
| `docs/CURRENT_STATE.md` | Updated stable baseline, runtime status, completed work, and active exclusions. |
| `docs/phase_plans/README.md` | Marked Phase 6 Web UI as complete. |
| `docs/phase_plans/phase6_implementation_plan.md` | Marked Web UI checklist items complete and recorded implementation results. |
| `CHANGELOG.md` | Added the `v6.0.0` Phase 6 Web UI entry. |

## Behavior

- `GET /` returns the static Web UI.
- The Web UI submits user questions through `POST /runs`.
- The Web UI polls `GET /runs/{run_id}` until a terminal status is reached.
- Final answers are rendered as Markdown using marked.js from a CDN.
- Status, token usage, cost, and a short run id suffix are shown in the UI.
- Channel behavior remains a thin adapter over the HTTP API. It does not call
  `run_agent()` directly and does not contain domain logic.
- Existing HTTP API behavior remains unchanged:
  - `POST /runs` still returns HTTP 503 when the service is not initialized.
  - `GET /runs/{run_id}` still returns HTTP 503 when not initialized and HTTP
    404 for missing runs.
  - `GET /runs/{run_id}/trace` still returns validated JSONL trace events.

## Guardrails preserved

- Single-agent runtime remains unchanged.
- No LangGraph or workflow orchestration engine was added.
- No write SQL tools or unrestricted SQL execution path was added.
- Redaction remains in the runtime and persistence layers.
- The channel adapter uses stored, already-redacted run output.
- Slack and scheduled report adapters remain optional and unimplemented.

## Test baseline

120 tests passing.

Commands used:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/test_api.py
UV_CACHE_DIR=/tmp/uv-cache uv run pytest
git diff --check
```

## Release label

`v6.0.0`
