# CLAUDE.md

## Rules

- Always read `SPEC.md` first.
- Then read `IMPLEMENTATION_PLAN.md`.
- Read the relevant `docs/*.md` files before editing implementation files.
- Use English for all repository Markdown.
- Implement only the currently requested phase.
- Current target is Phase 1 unless explicitly changed.
- Do not add LangGraph unless explicitly requested.
- Do not create write SQL tools.
- Do not create `execute_any_sql`.
- Preserve redaction before LLM input.
- Preserve redaction before trace persistence.
- Use read-only DB access assumptions.
- Use `sqlite3` CLI for local SQLite inspection when available, and avoid printing PII values in command output.
- Keep changes scoped to the requested step.
- Run pytest before declaring done.
- Treat `IMPLEMENTATION_PLAN.md` as the current execution state.
- Treat `IMPLEMENTATION_PLAN.md` as Phase 1 only.
- When a step is fully completed and verified, change its checkbox from `[ ]` to `[x]`.
- Do not mark a step complete until its listed work and relevant tests are done.
- Do not read or rely on `_archive/long_SPEC_archive.md` for implementation decisions.

## Context loading

- Load stable context first: `SPEC.md`, then `docs/00_project_overview.md`, then `docs/01_architecture_principles.md`.
- Load mutable context after stable context: `IMPLEMENTATION_PLAN.md`.
- Load only the topic-specific `docs/*.md` files needed for the current step.
- Prefer the split documents over archived material to avoid stale-spec conflicts.
- Do not add Phase 2+ tasks to `IMPLEMENTATION_PLAN.md`; create a separate plan when Phase 2 starts.

## Phase 1 guardrails

- Local CLI only.
- Single agent only.
- Markdown knowledge source only.
- Minimal direct agent loop.
- JSONL trace per run.
- Parser-backed read-only SQL validation.
- `input_hash` must track run conditions, not guarantee deterministic LLM output.
