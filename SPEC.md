# SPEC.md

## Project

Local-first domain expert AI agent MVP.

This file is the fixed entry point for humans and AI coding agents.
Detailed specifications live under `docs/`.

All repository Markdown must be written in English.

## Read order

1. `SPEC.md`
2. `docs/00_project_overview.md`
3. `docs/01_architecture_principles.md`
4. `docs/baselines/README.md`
5. `docs/phase_plans/README.md`

Read topic-specific documents as needed:

- Runtime loop / state / cost / input hash: `docs/03_runtime_loop.md`
- SQL tool / DB safety: `docs/04_tools_sql_security.md`
- Redaction / trace / response format: `docs/05_redaction_trace.md`
- Eval / pytest strategy: `docs/06_eval_strategy.md`
- Future scaling: `docs/07_future_scaling.md`
- Version 1 Phase 1 baseline: `docs/baselines/version1_phase1_baseline.md`
- Version 6 Phase 6 Web UI baseline: `docs/baselines/version6_phase6_web_ui_baseline.md`
- Phase 1 history: `docs/phase_plans/phase1_implementation_plan.md`
- Phase 2 completion summary: `docs/phase_plans/phase2_implementation_plan.md`

## Source of truth

- `_archive/long_SPEC_archive.md` preserves the previous complete SPEC v3.3 for human reference only.
- `SPEC.md` is the operational entry point.
- `docs/*.md` are the detailed working specifications.
- `docs/baselines/README.md` indexes completed baseline snapshots.
- `docs/phase_plans/README.md` indexes phase plan names, locations, statuses, and roles.
- `docs/phase_plans/phase1_implementation_plan.md` preserves the Phase 1 historical implementation plan.
- `docs/phase_plans/phase2_implementation_plan.md` preserves the Phase 2 completion summary.
- `IMPLEMENTATION_PLAN.md` is a compatibility pointer only.
- `CLAUDE.md` defines AI coding-agent guardrails.
- `CHANGELOG.md` records version history.

## Context loading

- Prefer `SPEC.md`, the current baseline, `docs/phase_plans/README.md`, and the relevant `docs/*.md` files.
- Do not use `_archive/long_SPEC_archive.md` as an implementation source.
- Treat `docs/00_project_overview.md` and `docs/01_architecture_principles.md` as stable context.
- Treat root `IMPLEMENTATION_PLAN.md` as a compatibility pointer, not as an active phase plan.

## Current baseline

Phase 4 SQLite FTS knowledge search is complete, and the Phase 6 Web UI channel adapter is complete.

## Must follow

- Use English for repository Markdown, prompts, comments in docs, and eval descriptions.
- Start local-first.
- Keep the current baseline single-agent.
- Use Markdown-centered knowledge, skills, and policies.
- Keep the minimal agent loop direct.
- Use read-only tools by default.
- Use a read-only DB user.
- Allow only read-only SQL.
- Validate SQL with a parser; do not rely only on string blocking.
- Redact SQL results before passing them to the LLM.
- Redact trace data before saving it.
- Save trace as JSONL per run.
- Save `input_hash` for run-condition tracking.
- Enforce max step, max token, and max cost limits.
- Keep channel adapters thin: Web UI and future channels must use the HTTP API instead of calling `run_agent()` directly.
- Run pytest before declaring implementation complete.

## Still out of scope

- LangGraph.
- Multi-agent orchestration.
- Vector databases or external search services.
- Slack bot and scheduled report channels unless explicitly requested.
- Write SQL tools.
- `execute_any_sql`.
- Production DB updates.
- Unredacted SQL result forwarding to the LLM.
- Unredacted trace persistence.

## Phase plan files

- `docs/phase_plans/phase1_implementation_plan.md` is the completed Phase 1 historical plan.
- `docs/phase_plans/phase2_implementation_plan.md` is the completed Phase 2 summary.
- `IMPLEMENTATION_PLAN.md` is a short compatibility pointer for older references.

When details are needed, read the relevant `docs/*.md` file for the area being changed.
