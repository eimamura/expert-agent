# docs/06_eval_strategy.md

## Role

This document defines eval, pytest, trace use, and quality checks.

## Read first

- `../SPEC.md`
- `docs/02_phase1_mvp_scope.md`
- `docs/04_tools_sql_security.md`
- `docs/05_redaction_trace.md`

## Related documents

- `phase_plans/phase1_implementation_plan.md`

## Implementation targets

- `domains/subscription_commerce/evals/*.jsonl`
- `tests/test_eval_runner.py`
- `tests/test_sql_safety.py`
- `tests/test_redaction.py`
- `tests/test_response_format.py`

---

# Eval Strategy

## Goal

Continuously verify agent quality and safety.

Phase 1 and Phase 2 should not depend on LLM-as-a-judge. Use deterministic tests first.

## Eval layers

1. Unit tests for safety-critical functions.
2. JSONL cases for expected tool use and response shape.
3. Trace-based checks for tool order, redaction, cost, and status.

## Eval JSONL shape

Recommended fields:

```json
{
  "id": "case_001",
  "question": "Which tables are needed to analyze monthly revenue?",
  "expected_tools": ["read_knowledge_file"],
  "forbidden_tools": ["run_write_sql"],
  "expected_response_sections": ["Summary", "Findings", "Evidence"],
  "tools_call_order": ["read_knowledge_file", "run_readonly_sql"]
}
```

## `tools_call_order`

`tools_call_order` is a partial-order expectation.

When duplicate tool calls exist, validation should use the first index at which each expected tool appears after the previous expected tool.

Pseudo-code:

```python
cursor = 0
for expected in tools_call_order:
    index = find_next(actual_tools, expected, start=cursor)
    assert index is not None
    cursor = index + 1
```

This allows additional calls between expected calls.

## SQL safety cases

`domains/subscription_commerce/evals/sql_safety_cases.jsonl` should include:

- allowed SELECT;
- multiple statements;
- INSERT;
- UPDATE;
- DELETE;
- DROP;
- DDL hidden in CTE;
- DML hidden in CTE;
- unapproved table;
- schema-less table reference;
- CTE alias handling;
- subquery table extraction.

## Domain cases

`domains/subscription_commerce/evals/domain_cases.jsonl` should include representative domain questions:

- definition questions;
- KPI interpretation questions;
- schema-discovery questions;
- investigation questions;
- evidence-required questions.

## Response format cases

`domains/subscription_commerce/evals/response_format_cases.jsonl` should verify that final answers include the required sections.

## Eval runner

`tests/test_eval_runner.py` should:

- load JSONL cases;
- validate required fields;
- run deterministic validation where possible;
- inspect recorded tool calls or trace fixtures;
- avoid requiring live LLM calls by default.

## Trace checks

Trace-based tests should verify:

- every event has `schema_version`;
- every event has `run_id`;
- timestamps are valid UTC ISO 8601;
- `run_finished.status` is an allowed value;
- tool output samples are redacted;
- SQL result PII is not persisted;
- cost and token fields are present for LLM calls.

## Phase 2 completion criteria

Phase 2 is complete in `docs/phase_plans/phase2_implementation_plan.md`.
The completed Phase 2 baseline satisfies:

- eval runner exists;
- SQL safety evals exist;
- response-format validation exists;
- trace validation exists;
- redaction tests are expanded;
- path traversal tests are expanded;
- SQL dialect tests exist;
- CTE extraction tests exist.
