# docs/phase_plans/phase6_implementation_plan.md

## Role

This document is the implementation plan for Phase 6: multiple channel integrations.

Phase 6 starts from the current HTTP API baseline. Phase 5 was intentionally
skipped because the trigger conditions for LangGraph were not met.

## Status

Phase 6 Web UI deliverable is complete. Optional Slack and scheduled report
adapters are not started.

## Objective

Expose the agent through more than one user channel. Channels are adapters around the same runtime — core agent logic is not duplicated per channel.

Reference: `docs/07_future_scaling.md` § Phase 6.

---

## Trigger conditions

Phase 6 should be started when any of the following apply:

- The HTTP API is stable and used in production
- A second consumer (Slack, scheduled report, internal tool) requests access
- The team wants to reduce manual CLI usage for recurring queries

---

## Scope

### Candidate channels

| Channel | Priority | Notes |
| --- | --- | --- |
| Web UI | High | Simple chat interface over the Phase 3 HTTP API |
| Slack bot | Medium | Slash command or mention triggers a run |
| Scheduled reports | Medium | Cron-triggered runs with result delivery |
| Internal tools | Low | Embed agent calls in existing dashboards |

### Architecture policy

All channels are thin adapters:

```
Channel adapter  →  POST /runs  →  runtime/loop.py  →  run_store + trace
```

- Channels must not call `run_agent()` directly — they must go through the HTTP API.
- No domain logic lives in a channel adapter.
- Channel-specific formatting (Slack markdown, HTML, plain text) happens in the adapter layer only.

### Phase 6 deliverable: Web UI

A minimal single-page chat UI served by FastAPI as a static file. Tech: plain HTML + JavaScript (`fetch`), no build step required.

- Text input for the question
- Submit button triggers `POST /runs`
- Polling `GET /runs/{run_id}` until terminal status
- Renders `final_answer` as Markdown
- Shows token usage and cost

---

## Completion checklist

- [x] Step 1: Add `GET /` route to `app/api.py` serving `app/static/index.html`.
- [x] Step 2: Create `app/static/index.html` — minimal chat UI (HTML + vanilla JS).
- [x] Step 3: Wire polling logic: `POST /runs` → poll `GET /runs/{id}` → display answer.
- [x] Step 4: Add Markdown rendering (marked.js CDN or equivalent).
- [ ] Step 5: (Optional) Slack adapter in `app/channels/slack.py` using Slack Bolt SDK.
- [ ] Step 6: (Optional) Scheduled report runner in `app/channels/scheduler.py`.
- [x] Step 7: Write tests for the Web UI route and static file serving.
- [x] Step 8: Update `docs/CURRENT_STATE.md` and this file.

---

## Guardrails inherited from Phase 5

- Channels must not bypass the HTTP API to call `run_agent()` directly.
- No write SQL tools introduced by channel adapters.
- Redaction must remain in the runtime layer — channels receive already-redacted output.
- No authentication secrets hardcoded in channel adapter code.

---

## Implementation Result

**Status:** Web UI complete

**Implemented files:**
- `app/api.py` — adds `GET /` serving the static Web UI from `app/static/index.html`.
- `app/static/index.html` — single-page vanilla HTML/JS UI that submits to `POST /runs`, polls `GET /runs/{run_id}`, renders Markdown with marked.js, and displays status, token usage, and cost.
- `tests/test_api.py` — covers the static HTML route and preserves existing `/runs` initialization behavior coverage.
- `docs/CURRENT_STATE.md` — records Phase 6 Web UI completion status.

**Deviations from plan:**
- No Phase 6 baseline snapshot was added, so `docs/baselines/README.md` was not changed.
- Slack and scheduled report adapters remain optional and out of scope for this Web UI deliverable.
- Phase 6 starts from the current HTTP API baseline because Phase 5 was skipped by ADR-0005.
