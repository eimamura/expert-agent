# IMPLEMENTATION_PLAN.md

## Role

This file defines the implementation order, completion criteria, and detailed specification references for the Phase 1 MVP.
It is both a procedure document and the execution-state file for implementation agents.
This file is Phase 1 only. Do not add Phase 2 or later work here.

## Read first

- `SPEC.md`
- `docs/00_project_overview.md`
- `docs/01_architecture_principles.md`
- `docs/02_phase1_mvp_scope.md`

## Implementation policy

- Execute steps in order from Step 0.
- Read the referenced documents before implementing each step.
- Do not implement features outside Phase 1.
- Add or update relevant tests for each step.
- Run pytest before declaring the implementation complete.
- When a step is completed, update its checkbox in the `Progress` section from `[ ]` to `[x]`.
- Do not mark an unverified step as `[x]`.

## Progress

- [ ] Step 0: Project baseline
- [ ] Step 1: Directory skeleton
- [ ] Step 2: Phase 0 knowledge files
- [ ] Step 3: Rules and eval seeds
- [ ] Step 4: Runtime config
- [ ] Step 5: Prompt contract
- [ ] Step 6: Run IDs
- [ ] Step 7: Input hashing
- [ ] Step 8: Cost tracking
- [ ] Step 9: Redaction
- [ ] Step 10: Knowledge loader
- [ ] Step 11: SQL safety
- [ ] Step 12: SQL execution wrapper
- [ ] Step 13: Trace writer
- [ ] Step 14: Agent loop
- [ ] Step 15: CLI
- [ ] Step 16: Output formatter
- [ ] Step 17: Eval runner
- [ ] Step 18: Test completion pass
- [ ] Step 19: Final verification

## Step 0: Project baseline

References:

- `docs/00_project_overview.md`
- `docs/02_phase1_mvp_scope.md`

Work:

- Create `pyproject.toml`.
- Require Python 3.10+.
- Use `uv`.
- Commit the generated lock file.
- Create `.env.example`.

## Step 1: Directory skeleton

References:

- `docs/00_project_overview.md`
- `docs/02_phase1_mvp_scope.md`

Work:

- Create `app/`, `agents/`, `runtime/`, `tools/`, `config/`, `knowledge/`, `skills/`, `policies/`, `rules/`, `evals/`, `memory/`, `traces/`, and `tests/`.
- Add `traces/.gitkeep`.

## Step 2: Phase 0 knowledge files

References:

- `docs/02_phase1_mvp_scope.md`

Work:

- Create `knowledge/domain_overview.md`.
- Create `knowledge/kpi_definitions.md`.
- Create `knowledge/database_schema.md`.
- Create `skills/investigation_skill.md`.
- Create `skills/sql_diagnosis_skill.md`.
- Create `skills/report_generation_skill.md`.
- Create `policies/db_safety.md`.
- Create `policies/production_change_policy.md`.
- Create `policies/response_policy.md`.

## Step 3: Rules and eval seeds

References:

- `docs/02_phase1_mvp_scope.md`
- `docs/04_tools_sql_security.md`
- `docs/05_redaction_trace.md`
- `docs/06_eval_strategy.md`

Work:

- Create `rules/allowed_tables.yml`.
- Create `rules/thresholds.yml`.
- Create `rules/redaction.yml`.
- Create `rules/pii_columns.yml`.
- Create `evals/seed_questions.jsonl`.
- Create `evals/sql_safety_cases.jsonl`.
- Create `evals/domain_cases.jsonl`.
- Create `evals/response_format_cases.jsonl`.

## Step 4: Runtime config

References:

- `docs/03_runtime_loop.md`

Work:

- Create `config/app.yml`.
- Implement `runtime/config.py`.
- Validate hard limits.
- Implement model alias resolution.
- Load pricing configuration.

## Step 5: Prompt contract

References:

- `docs/03_runtime_loop.md`
- `docs/05_redaction_trace.md`

Work:

- Create `agents/prompts.py`.
- Export `SYSTEM_PROMPT_TEMPLATE`.
- Keep the placeholder contract fixed.
- Use an English Phase 1 system prompt.

## Step 6: Run IDs

References:

- `docs/03_runtime_loop.md`
- `docs/05_redaction_trace.md`

Work:

- Implement `runtime/ids.py`.
- Generate ULID-based `run_id` values.

## Step 7: Input hashing

References:

- `docs/03_runtime_loop.md`
- `docs/05_redaction_trace.md`

Work:

- Implement `runtime/hashing.py`.
- Compute stable `input_hash` values.
- Support config snapshots.

## Step 8: Cost tracking

References:

- `docs/03_runtime_loop.md`

Work:

- Implement `runtime/cost.py`.
- Accumulate token and cost usage after each provider call.
- Enforce max token and max cost limits.

## Step 9: Redaction

References:

- `docs/05_redaction_trace.md`

Work:

- Implement `runtime/redaction.py`.
- Implement `redact_text()`.
- Implement `redact_sql_rows()`.
- Implement `RedactedSqlResult`.
- Add redaction tests.

## Step 10: Knowledge loader

References:

- `docs/03_runtime_loop.md`

Work:

- Implement `runtime/knowledge_loader.py`.
- Implement `list_knowledge_files()`.
- Implement `read_knowledge_file()`.
- Build a short Markdown knowledge index for prompt insertion.
- Include file paths, previews, byte sizes, and content hashes in the index source data.
- Prevent path traversal.
- Reject absolute paths.
- Enforce maximum file-read size.
- Add knowledge-loader and path-security tests.

## Step 11: SQL safety

References:

- `docs/04_tools_sql_security.md`

Work:

- Implement `tools/sql.py`.
- Implement `validate_readonly_sql()`.
- Implement `extract_tables()`.
- Support configured SQL dialects.
- Use parser-backed SELECT-only validation.
- Reject destructive AST nodes.
- Validate referenced tables against `rules/allowed_tables.yml`.
- Do not misclassify CTE names as physical tables.
- Reject schema-less table references in Phase 1.
- Add SQL validation and table-extraction tests.

## Step 12: SQL execution wrapper

References:

- `docs/04_tools_sql_security.md`
- `docs/05_redaction_trace.md`

Work:

- Assume read-only DB credentials.
- Implement `list_tables()`.
- Implement `get_table_schema()`.
- Implement `run_readonly_sql()`.
- Apply statement timeout settings.
- Enforce row and result-size limits.
- Redact SQL results before passing them to the LLM.
- Return useful metadata for trace events.
- Add SQL tool wrapper tests.

## Step 13: Trace writer

References:

- `docs/05_redaction_trace.md`

Work:

- Implement `runtime/trace.py`.
- Write `traces/{run_id}.jsonl`.
- Include common event fields: `schema_version`, `run_id`, `parent_run_id`, `event_type`, and `timestamp`.
- Emit `parent_run_id` as null in Phase 1.
- Use UTC ISO 8601 timestamps with at least millisecond precision.
- Support `run_started`, `llm_call`, `tool_call`, and `run_finished`.
- Include required per-event fields for each supported event type.
- Enforce the defined `run_finished.status` enum.
- Include token and cost fields for LLM calls and run completion.
- Include redacted tool arguments, redacted output samples, output sample strategy, output sample size, redacted columns, status, and error for tool calls.
- Redact events before writing them.
- Add trace schema and trace redaction tests.

## Step 14: Agent loop

References:

- `docs/03_runtime_loop.md`
- `docs/04_tools_sql_security.md`
- `docs/05_redaction_trace.md`

Work:

- Implement `runtime/loop.py`.
- Implement `runtime/state.py`.
- Build the minimal LLM -> tool -> LLM loop.
- Insert the rendered knowledge index into `SYSTEM_PROMPT_TEMPLATE`.
- Stop at max step.
- Stop when token or cost limits are exceeded.
- Truncate oversized tool results.

## Step 15: CLI

References:

- `docs/02_phase1_mvp_scope.md`
- `docs/03_runtime_loop.md`

Work:

- Implement `app/main.py`.
- Run the agent from a local CLI.
- Load config.
- Print the final response.

## Step 16: Output formatter

References:

- `docs/05_redaction_trace.md`

Work:

- Enforce these response sections:
  - Summary
  - Findings
  - Evidence
  - SQL / Tool Calls Used
  - Risks / Uncertainty
  - Recommended Next Actions
- Add response-format tests.

## Step 17: Eval runner

References:

- `docs/06_eval_strategy.md`

Work:

- Implement `tests/test_eval_runner.py`.
- Load JSONL eval cases.
- Validate `evals/seed_questions.jsonl`.
- Validate `evals/sql_safety_cases.jsonl`.
- Validate `evals/domain_cases.jsonl`.
- Validate `evals/response_format_cases.jsonl`.
- Support SQL safety cases.
- Support domain cases.
- Support response-format cases.
- Avoid requiring live LLM calls by default.

## Step 18: Test completion pass

References:

- All Phase 1 documents.

Work:

- Add path-traversal tests.
- Add SQL-safety tests.
- Add redaction tests.
- Add trace tests.
- Add response-format tests.
- Add knowledge-loader tests.
- Add tool tests.

## Step 19: Final verification

References:

- `docs/02_phase1_mvp_scope.md`

Work:

- Run the full pytest suite.
- Confirm the Phase 1 completion criteria.
- Confirm Phase 1 non-goals were not implemented.
- Update `CHANGELOG.md` if the specification changes.
