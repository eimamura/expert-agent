# docs/baselines/version2_phase2_baseline.md

## Purpose

Version 2 records the completed Phase 2 refinement: deterministic trace schema validation, provider test doubles, eval assertions, and runtime error normalization added on top of the Phase 1 MVP.

Phase 2 exists to make the agent loop testable without live LLM credentials and to enforce a validated trace contract before opening the service boundary in Phase 3. It is a comparison baseline for Phase 3, not a replacement for the detailed Phase 2 specifications in `docs/*.md`.

## Implemented Capabilities

All Phase 1 capabilities are preserved. Phase 2 adds:

- Pydantic trace schema validation in `runtime/trace_schema.py` — schema version `"1.0"` with four validated event shapes: `run_started`, `llm_call`, `tool_call`, `run_finished`.
- `NormalizedError` Pydantic model — `{type, message, retryable, source}` shape enforced on all runtime errors written to traces.
- `timeout_error` preserved as a terminal run status distinct from LLM or tool errors.
- `validate_trace_event()` and `validate_trace_events()` — per-event and full-trace validation with `TraceSchemaError` on schema mismatch or missing `run_finished`.
- Provider test doubles in `runtime/provider_double.py` — `ProviderDouble` with a scripted call sequence; `ScriptedProviderError` and `ScriptedProviderTimeout` exception types; `final_answer()` and `tool_request()` response builders.
- Trace reader and replay in `runtime/trace_reader.py` — `read_trace_jsonl()`, `load_validated_trace()`, and `assert_trace_replayable()`.
- Sensitive fixture marker check in `load_validated_trace()` — rejects traces containing known unredacted test values.
- Trace summary helpers in `runtime/trace_summary.py` — `summarize_trace()`.
- Eval assertions in `runtime/eval_assertions.py` — `assert_trace_case()`, `has_partial_order()`, `tool_names()`.
- Seven fixture traces under `fixtures/traces/`: `success_basic.jsonl`, `tool_error.jsonl`, `max_steps_exceeded.jsonl`, `max_cost_exceeded.jsonl`, `provider_error.jsonl`, `timeout_error.jsonl`, `validation_error.jsonl`.
- Deterministic runtime-loop tests using `ProviderDouble` — no live LLM credentials required by default tests.
- `ToolCallEvent` truncation fields: `tool_result_truncated`, `max_tool_result_bytes`, `observed_tool_result_bytes`.
- `RunFinishedEvent` `limit_metadata` field for budget overflow details.

## Trace Schema Structure

### Schema version

All trace events carry `schema_version: "1.0"`. Validation rejects any other value.

### Event types

| Event type | Key fields |
| --- | --- |
| `run_started` | `input_hash`, `config_snapshot`, `question` |
| `llm_call` | `provider`, `model_id`, `input_tokens`, `output_tokens`, `cost_usd`, `input_summary_redacted`, `output_summary_redacted` |
| `tool_call` | `tool_name`, `arguments_redacted`, `status`, `output_sample_redacted`, `output_sample_strategy`, `output_sample_size`, `redacted_columns`, `error`, `tool_result_truncated` |
| `run_finished` | `status`, `steps`, `total_input_tokens`, `total_output_tokens`, `total_cost_usd`, `error`, `limit_metadata` |

### NormalizedError

| Field | Allowed values |
| --- | --- |
| `type` | `provider_error`, `tool_error`, `validation_error`, `timeout_error`, `budget_error`, `internal_error` |
| `source` | `provider`, `tool`, `runtime`, `validator`, `budget`, `unknown` |
| `retryable` | `bool` |
| `message` | `str` |

### Run finished statuses

`success`, `tool_error`, `llm_error`, `timeout_error`, `max_steps_exceeded`, `max_tokens_exceeded`, `max_cost_exceeded`, `validation_error`.

### Timestamp format

All `timestamp` fields must be ISO 8601 UTC ending with `Z`. Validation rejects timestamps without `Z` or with a non-UTC offset.

## Safety and Guardrails

All Phase 1 guardrails are preserved unchanged. Phase 2 adds:

- Trace schema validation (`validate_trace_events`) prevents malformed or schema-mismatched events from being accepted by replay and eval tooling.
- `load_validated_trace()` rejects traces containing known sensitive fixture markers before schema validation, preventing inadvertent redaction bypass in test fixtures.
- `ProviderDouble` is a test-only component; the live Anthropic provider remains the only production call path.
- No new write SQL tools were introduced.
- No new production mutation paths were introduced.

## Known Limitations

Phase 1 limitations carried forward unchanged:

- The runtime is a single agent.
- The interface is local CLI only.
- There is no Web UI.
- There is no HTTP API.
- LangGraph is not used.
- There is no multi-agent orchestration.
- There is no vector database or external search infrastructure.
- Markdown retrieval is naive: files are listed and summarized, then explicitly read by tool call.
- The only implemented live provider wrapper is Anthropic.
- SQL execution currently supports SQLite only.
- Traces are local JSONL files with one file per run.
- Trace storage is not date-partitioned and is not externalized.
- `input_hash` tracks run conditions and does not guarantee deterministic LLM output.
- Regex text redaction is best-effort and may miss sensitive data.

Phase 2 additions:

- Provider calls do not have an explicit HTTP-layer timeout; `timeout_error` is propagated when the provider raises `TimeoutError` but is not independently enforced at the transport layer.

## Version 2 Baseline for Phase 3 Comparison

Phase 3 should preserve:

- Trace schema version `"1.0"` and the four-event shape contract.
- `NormalizedError` `{type, message, retryable, source}` shape for all runtime errors.
- Redaction before LLM-visible tool results.
- Redaction before trace event persistence.
- `load_validated_trace()` sensitive-marker check.
- Provider double interface for deterministic test coverage.
- Eval assertion API (`assert_trace_case`, `has_partial_order`, `tool_names`).
- Budget tracking fields in `RunFinishedEvent` (`total_input_tokens`, `total_output_tokens`, `total_cost_usd`, `limit_metadata`).
- `input_hash` as a run-condition identifier.
- Parser-backed read-only SQL validation.
- No write tools and no production mutation by default.
- Deterministic pytest coverage that does not require live LLM calls by default.

Phase 3 may improve:

- Run persistence in a database instead of trace JSONL only.
- HTTP API exposure for run creation and status retrieval.
- Asynchronous run execution.
- Trace partitioning and externalized storage.
- Explicit HTTP-layer timeout enforcement around provider calls.

Phase 3 may replace later:

- Local JSONL-only trace storage when a database-backed run store is introduced.
- The direct custom loop if a later phase explicitly introduces a workflow engine.
- SQLite-only execution when a production-safe read-only database target is introduced.
