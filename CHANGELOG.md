# CHANGELOG

This file records changes to the project specification and documentation.
The active implementation source is the split documentation set, starting from `SPEC.md`.

---

## v6.0.0 - 2026-05-02

Completed the Phase 6 Web UI channel adapter.

- Added `GET /` in `app/api.py` to serve the static Web UI.
- Added `app/static/index.html` as a vanilla HTML/JS UI that uses `POST /runs` and polls `GET /runs/{run_id}`.
- Added API coverage for static Web UI serving.
- Updated current-state and Phase 6 plan documentation.

---

## v3.10 - 2026-05-02

Fixed trace JSONL field ordering: `timestamp` is now the first key in every event.

- Changed `runtime/trace.py` from `sort_keys=True` to explicit `timestamp`-first ordering.

---

## v3.9 - 2026-05-02

Wired FastAPI lifespan to `init()` so `uvicorn app.api:app` works without a custom entrypoint.

- Added `_lifespan` context manager to `app/api.py`.
- Updated README with the direct uvicorn command.

---

## v3.8 - 2026-05-02

Organized phase plan documentation.

- Added `docs/phase_plans/README.md` as the phase plan index.
- Moved Phase 1 history to `docs/phase_plans/phase1_implementation_plan.md`.
- Moved Phase 2 status to `docs/phase_plans/phase2_implementation_plan.md` and compressed it into a completion summary.
- Moved Version 1 Phase 1 baseline to `docs/baselines/version1_phase1_baseline.md`.
- Replaced root `IMPLEMENTATION_PLAN.md` with a compatibility pointer.
- Updated read-order and source-of-truth references away from old active-plan paths.

---

## v3.7 - 2026-05-02

Added the Phase 2 preparation plan.

- Added `docs/phase_plans/phase2_implementation_plan.md` as a separate plan for trace, eval, and runtime refinement.
- Kept `docs/phase_plans/phase1_implementation_plan.md` scoped to Phase 1 history.
- Anchored Phase 2 planning to the `docs/baselines/version1_phase1_baseline.md` `v1.0.0` baseline.
- Preserved Phase 1 guardrails in the Phase 2 planning scope.

---

## v3.6 - 2026-05-02

Clarified Phase 1 documentation after implementation-plan review.

- Standardized dependency management on `uv`.
- Changed the SQL execution wrapper contract to return redacted rows plus metadata.
- Removed Phase 1 repository-structure placeholders that were not in the plan.
- Clarified that the final test pass audits and fills gaps instead of deferring all tests.

---

## v3.5 - 2026-05-02

Converted all repository Markdown files to English-only.

- Rewrote the Phase 1 implementation plan in English.
- Rewrote all `docs/*.md` files in English.
- Rewrote the archived long spec in English-summary form.
- Added an explicit English-only language policy.
- Updated the prompt contract to use an English Phase 1 system prompt.

---

## v3.4 - 2026-05-02

Split the previous single large `SPEC.md` into an entry file, detailed topic documents, a Phase 1 implementation plan, and AI coding-agent rules.

- Preserved the previous complete SPEC v3.3 under `_archive/long_SPEC_archive.md`.
- Changed `SPEC.md` into a short operational entry point.
- Split details into `docs/00_project_overview.md` through `docs/07_future_scaling.md`.
- Added `docs/phase_plans/phase1_implementation_plan.md` and fixed Phase 1 implementation order as Step 0 through Step 19.
- Added `CLAUDE.md` as coding-agent guardrails.
- Added checklist-based progress handling to `docs/phase_plans/phase1_implementation_plan.md`.
- Clarified that `docs/phase_plans/phase1_implementation_plan.md` is Phase 1 only.
- Added ignore files so `_archive/` is excluded from Claude, Cursor, and Codex exploration.

---

## v3.3 - 2026-05-02

Merged senior-review feedback into the main specification and moved version history into this changelog.

### Critical

- Fixed the expected `sqlglot` `walk()` API usage.
- Clarified that `redact_text()` is best-effort and that explicit PII column configuration is the primary protection.
- Added `redacted_columns` metadata to SQL redaction output and trace events.

### High

- Defined duplicate handling for `tools_call_order`.
- Added `schema_version` to trace events and made `parent_run_id` optional.
- Raised `max_run_cost_usd` from 1.0 to 3.0.
- Clarified trace file append and concurrency rules.
- Clarified that `input_hash` identifies run conditions, not deterministic LLM output.

### Medium

- Required concrete `model_id` values in production config snapshots.
- Rejected schema-less SQL table references in Phase 1.
- Added `database.statement_timeout_seconds`.
- Fixed the `list_knowledge_files()` return shape.

### Low

- Documented the default output sample size.
- Added the `agents/prompts.py` contract.
- Unified Phase 0 seed question schema with the later eval schema.

---

## v3.2 - 2026-05-02

Older revision.

- Switched SQL validation to AST walking.
- Rejected absolute paths in `validate_knowledge_path()`.
- Clarified pricing lookup normalization.
- Added output-token and tool-result byte limits.
- Fixed `run_finished.status` values.
- Defined output sampling.
- Specified SQL row redaction behavior.
- Corrected `input_hash` scope.
- Added knowledge file read limits.
- Standardized trace timestamps.

---

## v3.1 - 2026-05

Older revision.

- Clarified `config_snapshot`.
- Standardized UTC timestamps.
- Documented Phase 1 redaction limits.
- Clarified subquery table extraction.
- Isolated ULID usage in `runtime/ids.py`.
- Left date-partitioned trace directories as a future TODO.

---

## v3.0 - Initial

- Established the Phase 0 through Phase 7 roadmap.
- Defined the local-first MVP direction.
- Introduced the minimal agent loop, Markdown knowledge, read-only tools, redaction, trace, and eval strategy.
