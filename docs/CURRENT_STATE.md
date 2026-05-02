# docs/CURRENT_STATE.md

**Last Updated:** 2026-05-02
**Current Phase:** Phase 3 (Complete)

---

## Quick Status

| Item | Value |
| --- | --- |
| Stable baseline | `docs/baselines/version3_phase3_baseline.md` |
| Latest git tag | `v3.0.0` |
| Active task | `docs/phase_plans/phase6_implementation_plan.md` (Web UI — channel adapter) |
| Runtime | CLI + FastAPI HTTP API, single-agent, Anthropic provider |

## What is complete

- **Phase 1** — CLI MVP: domain pack loading, Markdown knowledge, read-only SQL, redaction, JSONL trace, basic evals. See `docs/baselines/version1_phase1_baseline.md`.
- **Phase 2** — Trace schema validation, provider test doubles, eval assertions, normalized error metadata. See `docs/baselines/version2_phase2_baseline.md`.
- **Phase 3** — FastAPI HTTP API (`POST /runs`, `GET /runs/{id}`, `GET /runs/{id}/trace`), SQLite run persistence, async background execution. See `docs/baselines/version3_phase3_baseline.md`.

## What is next

**Phase 6: Web UI** (`docs/phase_plans/phase6_implementation_plan.md`)

- Minimal HTML + vanilla JS chat UI served by FastAPI
- Channels call `POST /runs` → poll `GET /runs/{id}` → render answer
- Phase 5 (LangGraph) skipped — trigger conditions not yet met. See `docs/decisions/ADR-0005-skip-phase5-langgraph.md`.
- Phase 4 (SQLite FTS) also deferred — knowledge base still small enough for naive retrieval.

## Routing

| Goal | Where to look |
| --- | --- |
| Understand the current architecture | `docs/baselines/version3_phase3_baseline.md` |
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
- Web UI
- Write / UPDATE / DELETE SQL tools
- `execute_any_sql` or equivalent unrestricted tool
- Vector database or external search infrastructure
- Production database mutation
