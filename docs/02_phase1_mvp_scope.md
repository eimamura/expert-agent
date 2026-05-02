# docs/02_phase1_mvp_scope.md

## Role

This document defines Phase 0 and Phase 1 MVP scope, non-goals, and completion criteria.

## Read first

- `../SPEC.md`
- `docs/00_project_overview.md`
- `docs/01_architecture_principles.md`

## Related documents

- `phase_plans/phase1_implementation_plan.md`
- `docs/03_runtime_loop.md`
- `docs/04_tools_sql_security.md`
- `docs/05_redaction_trace.md`
- `docs/06_eval_strategy.md`

## Implementation targets

- `domains/subscription_commerce/knowledge/`
- `domains/subscription_commerce/skills/`
- `domains/subscription_commerce/policies/`
- `domains/subscription_commerce/rules/`
- `domains/subscription_commerce/evals/`
- `app/main.py`
- `agents/`
- `runtime/`
- `tools/`
- `tests/`

---

# Phase 0: Markdown Knowledge Base Design

## Goal

Organize knowledge, procedures, and decision criteria as Markdown and YAML.

Phase 0 does not build the runtime. The goal is not to create many files for their own sake, but to create enough structure to answer expected questions.

## Required files

### `domains/subscription_commerce/knowledge/`

- `domain_overview.md`: domain concepts, business context, terminology, and common questions.
- `kpi_definitions.md`: metric definitions, calculation formulas, interpretation notes, and caveats.
- `database_schema.md`: table descriptions, key columns, joins, and known data-quality issues.

### `domains/subscription_commerce/skills/`

- `investigation_skill.md`: how the agent should investigate a question.
- `sql_diagnosis_skill.md`: how the agent should inspect data with SQL.
- `report_generation_skill.md`: how the agent should structure final answers.

### `domains/subscription_commerce/policies/`

- `db_safety.md`: allowed and forbidden DB behavior.
- `production_change_policy.md`: production mutation is forbidden in Phase 1.
- `response_policy.md`: evidence, uncertainty, and recommendation rules.

### `domains/subscription_commerce/rules/`

- `allowed_tables.yml`: approved tables.
- `thresholds.yml`: project-specific thresholds.
- `redaction.yml`: text redaction patterns.
- `pii_columns.yml`: columns that must be redacted in SQL results.

### `domains/subscription_commerce/evals/seed_questions.jsonl`

Initial expected questions should use the same shape as later eval cases:

```json
{"id":"seed_001","question":"What changed in monthly revenue?","expected_tools":["read_knowledge_file"],"expected_response_sections":["Summary","Findings","Evidence","Risks / Uncertainty"]}
```

## Phase 0 completion criteria

- Required knowledge files exist.
- Required skill files exist.
- Required policy files exist.
- Required rule files exist.
- Seed questions exist.
- The file set is enough to support realistic Phase 1 questions.

---

# Phase 1: Local Minimal Agent Loop

## Goal

Build a local CLI agent that can answer domain questions by using Markdown knowledge and safe read-only tools.

## Phase 1 must implement

- Local CLI execution.
- One agent.
- Direct provider SDK calls.
- A minimal custom agent loop.
- Markdown knowledge indexing.
- `read_knowledge_file()` tool.
- Path traversal protection.
- Read-only SQL tool.
- Parser-backed SQL validation.
- Allowed table validation.
- SQL result redaction before LLM input.
- JSONL trace per run.
- Trace redaction before persistence.
- `input_hash`.
- ULID `run_id`.
- Max step, token, and cost limits.
- Basic pytest-backed evals.

## Phase 1 must not implement

- LangGraph.
- Multi-agent orchestration.
- Web UI.
- HTTP API.
- Vector DB.
- External search infrastructure.
- Write SQL tools.
- Production updates.
- `execute_any_sql`.

## CLI target

`app/main.py` should support local execution such as:

```bash
python -m app.main "Explain the trend in active customers."
```

The CLI should:

- load config;
- build the knowledge index;
- start a run with a ULID `run_id`;
- execute the minimal loop;
- write trace events;
- print the final answer.

## Response format

Final answers must include:

- Summary
- Findings
- Evidence
- SQL / Tool Calls Used
- Risks / Uncertainty
- Recommended Next Actions

## Phase 1 completion criteria

- The agent can run from the CLI.
- The Markdown index can be inserted into the system prompt.
- The agent can call `read_knowledge_file()`.
- `read_knowledge_file()` prevents path traversal.
- `read_knowledge_file()` rejects absolute paths.
- `read_knowledge_file()` enforces `max_file_read_bytes`.
- The read-only SQL tool can run approved SELECT queries.
- DB access assumes a read-only user.
- SQL dialect is configurable.
- SQL validation rejects non-SELECT statements.
- SQL validation rejects destructive AST nodes.
- `WITH ... SELECT` is allowed when safe.
- DML or DDL inside `WITH` is rejected.
- References outside `allowed_tables.yml` are rejected.
- `extract_tables()` does not treat CTE names as physical tables.
- SQL results are redacted before LLM input.
- PII columns are redacted by exact key match using `pii_columns.yml`.
- Oversized tool results are truncated.
- The loop stops at max step.
- Token and cost usage are accumulated after each provider call.
- `max_output_tokens_per_call` limits each LLM call.
- Pricing is loaded from config.
- Pricing lookup resolves `model_id` first and model alias second.
- The run stops at max cost.
- `run_id` is generated as a ULID.
- Trace is saved to `traces/{run_id}.jsonl`.
- Trace events are redacted before persistence.
- `parent_run_id` is emitted as null in Phase 1.
- `run_finished.status` uses the defined enum.
- Trace timestamps are UTC ISO 8601 with at least millisecond precision.
- `input_hash` is saved according to spec.
- The final answer includes evidence.
- pytest passes.

## Phase 1 backlog

High priority:

- `app/main.py`
- `runtime/loop.py`
- `runtime/config.py`
- `runtime/cost.py`
- pricing loading
- model alias resolution
- `runtime/ids.py`
- `runtime/hashing.py`
- `runtime/redaction.py`
- `config/app.yml`
- `runtime/knowledge_loader.py`
- `read_knowledge_file()` tool
- path traversal tests
- `tools/sql.py`
- read-only DB connection assumptions
- parser-backed SQL validation
- `extract_tables()`
- SQL dialect config
- SQL-result redaction
- `runtime/trace.py`

Medium priority:

- `.env.example`
- output formatter

Low priority:

- trace pretty-printer
- date-partitioned trace directory TODO
