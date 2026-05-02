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
4. `docs/02_phase1_mvp_scope.md`
5. `IMPLEMENTATION_PLAN.md`

Read topic-specific documents as needed:

- Runtime loop / state / cost / input hash: `docs/03_runtime_loop.md`
- SQL tool / DB safety: `docs/04_tools_sql_security.md`
- Redaction / trace / response format: `docs/05_redaction_trace.md`
- Eval / pytest strategy: `docs/06_eval_strategy.md`
- Future scaling: `docs/07_future_scaling.md`

## Source of truth

- `_archive/long_SPEC_archive.md` preserves the previous complete SPEC v3.3 for human reference only.
- `SPEC.md` is the operational entry point.
- `docs/*.md` are the detailed working specifications.
- `IMPLEMENTATION_PLAN.md` defines Phase 1 implementation order only.
- `CLAUDE.md` defines AI coding-agent guardrails.
- `CHANGELOG.md` records version history.

## Context loading

- Prefer `SPEC.md`, `IMPLEMENTATION_PLAN.md`, and the relevant `docs/*.md` files.
- Do not use `_archive/long_SPEC_archive.md` as an implementation source.
- Treat `docs/00_project_overview.md` and `docs/01_architecture_principles.md` as stable context.
- Treat `IMPLEMENTATION_PLAN.md` as mutable execution state.

## Current target

Phase 1 only.

## Must follow

- Use English for repository Markdown, prompts, comments in docs, and eval descriptions.
- Start local-first.
- Use a single agent in Phase 1.
- Use Markdown-centered knowledge, skills, and policies.
- Implement the minimal agent loop directly.
- Use read-only tools by default.
- Use a read-only DB user.
- Allow only read-only SQL.
- Validate SQL with a parser; do not rely only on string blocking.
- Redact SQL results before passing them to the LLM.
- Redact trace data before saving it.
- Save trace as JSONL per run.
- Save `input_hash` for run-condition tracking.
- Enforce max step, max token, and max cost limits.
- Run pytest before declaring implementation complete.

## Must not implement in Phase 1

- LangGraph.
- Multi-agent orchestration.
- Web UI.
- HTTP API.
- Vector DB or external search infrastructure.
- Write SQL tools.
- `execute_any_sql`.
- Production DB updates.
- Unredacted SQL result forwarding to the LLM.
- Unredacted trace persistence.

## Implementation target

Follow `IMPLEMENTATION_PLAN.md` step by step for Phase 1.
When details are needed, read the relevant `docs/*.md` file named in that step.
