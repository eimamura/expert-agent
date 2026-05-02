# docs/CURRENT_STATE.md

**Last Updated:** 2026-05-02
**Current Phase:** Phase 6 Web UI (Complete)

---

## Quick Status

| Item | Value |
| --- | --- |
| Stable baseline | `docs/baselines/version6_phase6_web_ui_baseline.md` |
| Latest git tag | `v4.0.0` |
| Active task | Phase 6 Web UI deliverable complete; optional channels not started |
| Runtime | CLI + FastAPI HTTP API + static Web UI, single-agent, Anthropic provider |
| Domain instructions | `skills/*.md` and `policies/*.md` are injected into each run's system prompt |

## What is complete

- **Phase 1** — CLI MVP: domain pack loading, Markdown knowledge, read-only SQL, redaction, JSONL trace, basic evals. See `docs/baselines/version1_phase1_baseline.md`.
- **Phase 2** — Trace schema validation, provider test doubles, eval assertions, normalized error metadata. See `docs/baselines/version2_phase2_baseline.md`.
- **Phase 3** — FastAPI HTTP API (`POST /runs`, `GET /runs/{id}`, `GET /runs/{id}/trace`), SQLite run persistence, async background execution. See `docs/baselines/version3_phase3_baseline.md`.
- **Phase 4** — `SearchBackend` Protocol, `NaiveBackend`, `SqliteFtsBackend` (FTS5), `search_knowledge` tool, pluggable config. See `docs/baselines/version4_phase4_baseline.md`.
- **Phase 6 Web UI** — FastAPI-served static HTML UI at `GET /` that calls `POST /runs`, polls `GET /runs/{id}`, and renders final answers, status, token usage, and cost. See `docs/baselines/version6_phase6_web_ui_baseline.md`.
- **Domain instruction injection** — Domain pack `skills/` and `policies/` Markdown files are loaded in deterministic order and included in the system prompt for every CLI, API, and Web UI run.

## What is next

**Phase 6 optional channels or Phase 7 planning**

- Optional Slack and scheduled report adapters remain unimplemented.
- Phase 7 platform work remains provisional until operational needs are clear.
- Phase 5 (LangGraph) skipped — trigger conditions not yet met. See `docs/decisions/ADR-0005-skip-phase5-langgraph.md`.
- External search beyond local SQLite FTS remains deferred until operational need is clear.

## Routing

| Goal | Where to look |
| --- | --- |
| Understand the current architecture | `docs/baselines/version6_phase6_web_ui_baseline.md` |
| Write new code for Phase 4 | `docs/phase_plans/phase4_implementation_plan.md` |
| Plan for Phase 5 (LangGraph) | `docs/phase_plans/phase5_implementation_plan.md` |
| Plan for Phase 6 (Web UI / channels) | `docs/phase_plans/phase6_implementation_plan.md` |
| Plan for Phase 7 (agent platform) | `docs/phase_plans/phase7_implementation_plan.md` |
| Understand why domains/ exists | `docs/decisions/ADR-0001-domain-packs.md` |
| Understand why LangGraph is excluded | `docs/decisions/ADR-0002-no-langgraph-until-phase5.md` |
| Understand why write SQL is excluded | `docs/decisions/ADR-0003-read-only-sql.md` |
| Understand why Markdown first | `docs/decisions/ADR-0004-markdown-first-knowledge.md` |
| Phase history | `docs/phase_plans/README.md` |

## Active exclusions

Do NOT implement unless explicitly requested:

- LangGraph or any workflow orchestration engine
- Multi-agent orchestration
- Slack bot or scheduled report channels
- Write / UPDATE / DELETE SQL tools
- `execute_any_sql` or equivalent unrestricted tool
- Vector database or external search infrastructure
- Production database mutation
