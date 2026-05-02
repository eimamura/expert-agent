# CLAUDE.md

## Rules

- Always read `SPEC.md` first.
- Then read `docs/00_project_overview.md` and `docs/01_architecture_principles.md`.
- For current baseline context, read `docs/baselines/README.md` and `docs/phase_plans/README.md`.
- Read `docs/phase_plans/phase2_implementation_plan.md` for the Phase 2 completion summary.
- Read `docs/phase_plans/phase1_implementation_plan.md` only for Phase 1 history.
- Read the relevant `docs/*.md` files before editing implementation files.
- Use English for all repository Markdown.
- Implement only the currently requested phase.
- The current implemented baseline includes Phase 2 trace, eval, and runtime refinement.
- Do not add LangGraph unless explicitly requested.
- Do not create write SQL tools.
- Do not create `execute_any_sql`.
- Preserve redaction before LLM input.
- Preserve redaction before trace persistence.
- Use read-only DB access assumptions.
- Use `sqlite3` CLI for local SQLite inspection when available, and avoid printing PII values in command output.
- Keep changes scoped to the requested step.
- Run pytest before declaring done.
- Treat root `IMPLEMENTATION_PLAN.md` as a compatibility pointer only.
- Treat `docs/phase_plans/phase1_implementation_plan.md` as the completed Phase 1 historical plan.
- Treat `docs/phase_plans/phase2_implementation_plan.md` as the completed Phase 2 summary.
- When a requested future phase plan has checkboxes, do not mark a step complete until its listed work and relevant tests are done.
- Do not read or rely on `_archive/long_SPEC_archive.md` for implementation decisions.

## Context loading

- Load stable context first: `SPEC.md`, then `docs/00_project_overview.md`, then `docs/01_architecture_principles.md`.
- Load current baseline context after stable context: `docs/baselines/README.md`, then `docs/phase_plans/README.md`.
- Load a phase-specific plan only when the user explicitly requests work in that phase or the task directly concerns that phase's history.
- Load only the topic-specific `docs/*.md` files needed for the current step.
- Prefer the split documents over archived material to avoid stale-spec conflicts.
- Do not add Phase 2+ tasks to `docs/phase_plans/phase1_implementation_plan.md`.

## Current guardrails

- Local CLI only.
- Single agent only.
- Markdown knowledge remains a supported source.
- Minimal direct agent loop.
- JSONL trace per run.
- Parser-backed read-only SQL validation.
- `input_hash` must track run conditions, not guarantee deterministic LLM output.
- Default tests must not require live LLM credentials or a production database.
- Use provider test doubles for deterministic runtime-loop tests.
- Validate trace fixtures without calling providers, tools, or databases.
- Keep normalized trace errors in `{type, message, retryable, source}` shape.
- Preserve `timeout_error` as the provider/runtime timeout terminal status.
