# docs/05_redaction_trace.md

## Role

This document defines redaction, trace, `input_hash`, and response-format requirements.

## Read first

- `../SPEC.md`
- `docs/02_phase1_mvp_scope.md`
- `docs/03_runtime_loop.md`

## Related documents

- `docs/04_tools_sql_security.md`
- `docs/06_eval_strategy.md`

## Implementation targets

- `runtime/redaction.py`
- `runtime/trace.py`
- `runtime/hashing.py`
- `domains/subscription_commerce/rules/redaction.yml`
- `domains/subscription_commerce/rules/pii_columns.yml`
- `traces/`
- `tests/test_redaction.py`
- `tests/test_response_format.py`

---

# Redaction

## Goal

Prevent secrets, credentials, and personally identifiable information from being passed to the LLM or persisted in traces.

## Phase 1 policy

Phase 1 uses two layers:

1. Column-based SQL row redaction using `domains/subscription_commerce/rules/pii_columns.yml`.
2. Best-effort text redaction using configured patterns from `domains/subscription_commerce/rules/redaction.yml`.

Column-based SQL redaction is the stronger protection for structured results. Regex-based text redaction is explicitly best-effort and may miss sensitive data.

## `redact_text()`

`redact_text(text: str) -> str` should:

- apply configured secret and PII patterns;
- replace matched values with `[REDACTED]`;
- be safe to run on arbitrary strings;
- never raise on malformed input unless the caller passes a non-string programming error.

It is not a complete privacy system.

## `redact_sql_rows()`

Expected API:

```python
class RedactedSqlResult(TypedDict):
    rows: list[dict]
    redacted_columns: list[str]
    row_count: int
    truncated: bool

def redact_sql_rows(rows: list[dict], pii_columns: set[str]) -> RedactedSqlResult:
    ...
```

Rules:

- Match PII columns by exact key.
- Preserve non-PII values.
- Replace PII values with `[REDACTED]`.
- Preserve the row structure.
- Handle nested dictionaries and lists when they appear.
- Preserve value types for non-redacted values.
- Return `redacted_columns`.
- Return row count and truncation metadata.

## LLM-visible SQL result shape

The LLM should receive the redacted result, not the raw result.

Example:

```json
{
  "rows": [
    {"customer_id": 123, "email": "[REDACTED]", "monthly_revenue": 42.5}
  ],
  "redacted_columns": ["email"],
  "row_count": 1,
  "truncated": false
}
```

The system prompt must tell the agent that redacted columns cannot support value-level analysis.

---

# Trace

## `runtime/trace.py`

Trace files are written as JSONL:

```text
traces/{run_id}.jsonl
```

Phase 1 uses one trace file per run.

## File writing rules

- Open in append mode.
- Use line-buffered writes where practical.
- One run writes one file.
- Do not design for multiple processes writing the same trace file in Phase 1.

## Common event fields

Every trace event must include:

- `schema_version`
- `run_id`
- `parent_run_id`
- `event_type`
- `timestamp`

`schema_version` starts as `"1.0"`.

`parent_run_id` is optional conceptually, but Phase 1 should emit it as null for compatibility with later nested or multi-agent runs.

Timestamps must be UTC ISO 8601 strings with at least millisecond precision.

## `run_started`

Required fields:

- common fields
- `input_hash`
- `config_snapshot`
- `question`

## `llm_call`

Required fields:

- common fields
- `provider`
- `model_id`
- `input_tokens`
- `output_tokens`
- `cost_usd`
- redacted input or input summary
- redacted output or output summary

## `tool_call`

Required fields:

- common fields
- `tool_name`
- `arguments_redacted`
- `status`
- `output_sample_redacted`
- `output_sample_strategy`
- `output_sample_size`
- `redacted_columns`
- `error`

`output_sample_strategy` is `"head"` in Phase 1.
`output_sample_size` defaults to 5.

## `run_finished`

Required fields:

- common fields
- `status`
- `steps`
- `total_input_tokens`
- `total_output_tokens`
- `total_cost_usd`
- `error`

Allowed `status` values:

- `success`
- `max_steps_exceeded`
- `max_tokens_exceeded`
- `max_cost_exceeded`
- `tool_error`
- `llm_error`
- `validation_error`

## Trace requirements

- Redact before writing.
- Do not store raw SQL result rows containing PII.
- Store enough metadata to debug tool use.
- Store enough cost and token data to understand run budget behavior.
- Store `input_hash`.
- Store config snapshot fields that affect replay conditions.

## Future trace TODOs

Later phases may add:

- date-partitioned trace directories;
- external trace storage;
- trace replay UI;
- Langfuse or another observability backend;
- parent/child run propagation.

---

# Response Format

Final answers must use these sections:

## Summary

Short direct answer.

## Findings

Key observations and conclusions.

## Evidence

Markdown files, SQL results, or tool outputs that support the answer.

## SQL / Tool Calls Used

List tools and SQL queries used. Do not expose secrets.

## Risks / Uncertainty

State missing data, assumptions, redaction limits, or ambiguity.

## Recommended Next Actions

Practical next steps.
