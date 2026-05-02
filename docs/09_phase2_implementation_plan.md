# docs/09_phase2_implementation_plan.md

## Role

This file defines the proposed implementation order, scope boundaries, and verification requirements for **Phase 2**.

It is a planning document for **trace, eval, and runtime refinement** after the Phase 1 `v1.0.0` baseline.

This file does **not** replace `IMPLEMENTATION_PLAN.md`.

`IMPLEMENTATION_PLAN.md` remains the Phase 1 historical execution-state file and must not receive Phase 2 tasks.

---

## Read first

* `SPEC.md`
* `docs/00_project_overview.md`
* `docs/01_architecture_principles.md`
* `docs/08_version1_phase1_baseline.md`

---

## Related documents

* `docs/03_runtime_loop.md`
* `docs/04_tools_sql_security.md`
* `docs/05_redaction_trace.md`
* `docs/06_eval_strategy.md`
* `docs/07_future_scaling.md`

---

# Phase 2 Implementation Plan

## Baseline

Phase 2 starts from the released Phase 1 `v1.0.0` baseline recorded in:

```text
docs/08_version1_phase1_baseline.md
```

Use that document as the comparison point for:

```text
behavior
guardrails
known limitations
runtime assumptions
trace format
eval assumptions
```

Phase 2 improves confidence and debuggability without changing the product surface into a service or platform.

---

# Scope

## Phase 2 focuses on

```text
trace validation, replay, and analysis
expanded deterministic evals
runtime error handling and timeout behavior
provider test doubles
clearer cost, token, and tool-limit reporting
additional safety tests for SQL, redaction, and path handling
```

---

## Phase 2 preserves

```text
local-first CLI support
single-agent runtime
curated Markdown knowledge as a supported source
parser-backed read-only SQL validation
allowlisted schema-qualified table access
redaction before LLM input
redaction before trace persistence
JSONL trace output per run
input_hash as a run-condition identifier
no write tools
no production mutation by default
no live LLM calls required by default test commands
```

---

## Phase 2 does not introduce

```text
Web UI
HTTP API
LangGraph
external search infrastructure
vector database
multi-agent orchestration
write SQL tools
unrestricted SQL execution
production mutations
```

---

# Implementation Policy

* Keep Phase 2 runtime changes compatible with the Phase 1 local CLI workflow.
* Prefer deterministic unit tests and fixture-based integration tests.
* Use provider test doubles for runtime-loop behavior.
* Do not require live provider credentials for default verification.
* Keep trace data redacted at every persistence boundary.
* Keep SQL validation parser-backed and table-allowlist based.
* Keep runtime changes small and explicit.
* Do not introduce a workflow engine in Phase 2.
* Run `uv run pytest` before declaring Phase 2 implementation work complete.

---

# Phase 2 Additional Decisions

These decisions remove ambiguity for implementation.

## Provider test doubles

Provider test doubles should be implemented before runtime timeout, error, and budget tests.

Reason:

```text
timeout behavior
provider errors
budget stops
tool-call sequences
```

should be tested deterministically without live LLM calls.

---

## Trace schema validation

Trace schema validation should use **Pydantic models** in Phase 2.

Do not introduce:

```text
external schema registry
remote validation service
observability platform dependency
```

Suggested files:

```text
runtime/trace_schema.py
tests/test_trace_schema.py
```

---

## Replay definition

Phase 2 replay means **trace replay only**.

It must not:

```text
call a live LLM
re-execute tools
connect to a database
mutate files
mutate external systems
```

Trace replay should only read existing trace JSONL files and validate or summarize their structure.

---

## Allowed `run_finished.status` values

Use the existing Phase 1 enum values:

```text
success
max_steps_exceeded
max_tokens_exceeded
max_cost_exceeded
tool_error
llm_error
validation_error
```

Do not introduce ad-hoc status values such as:

```text
error
timeout
done
ok
```

unless the enum is explicitly updated.

Phase 2 timeout handling may add `timeout_error` as a terminal `run_finished.status`, but the trace writer and schema validator status enum must be updated before emitting timeout traces with that status.

---

## Normalized error metadata

Runtime errors should be normalized into this shape:

```json
{
  "error": {
    "type": "provider_error",
    "message": "redacted message",
    "retryable": false,
    "source": "provider"
  }
}
```

Required fields:

```text
type
message
retryable
source
```

Allowed `error.type` values:

```text
provider_error
tool_error
validation_error
timeout_error
budget_error
internal_error
```

Allowed `error.source` values:

```text
provider
tool
runtime
validator
budget
unknown
```

All error messages written to trace must be redacted before persistence.

---

## Tool result size limits

If not already present in Phase 1, Phase 2 may introduce:

```yaml
runtime:
  max_tool_result_rows: 100
  max_tool_result_chars: 20000
```

These limits should protect:

```text
LLM context size
trace size
cost growth
accidental large result dumps
```

Tool result truncation must be explicit in trace metadata.

---

## Eval distinction

Step 8 and Step 9 have different purposes.

```text
Step 8 = expand local eval case datasets
Step 9 = implement trace-based assertions over those cases
```

Do not merge them into a single vague eval task.

---

# Progress

```text
[ ] Step 0: Phase 2 planning baseline
[ ] Step 1: Provider test doubles
[ ] Step 2: Trace schema validation
[ ] Step 3: Trace replay fixtures
[ ] Step 4: Trace analysis helpers
[ ] Step 5: Runtime timeout handling
[ ] Step 6: Runtime error reporting
[ ] Step 7: Limit reporting improvements
[ ] Step 8: Expanded eval case coverage
[ ] Step 9: Trace-based eval assertions
[ ] Step 10: SQL dialect and CTE coverage
[ ] Step 11: Path traversal coverage
[ ] Step 12: Redaction regression coverage
[ ] Step 13: Phase 2 verification pass
```

---

# Step 0: Phase 2 Planning Baseline

## References

* `docs/08_version1_phase1_baseline.md`
* `docs/06_eval_strategy.md`

## Work

* Add this Phase 2 plan as a separate document.
* Keep `IMPLEMENTATION_PLAN.md` unchanged.
* Use the Phase 1 `v1.0.0` baseline for comparison.
* Confirm Phase 2 scope excludes:

```text
Web/API
LangGraph
external search
multi-agent orchestration
write tools
production mutations
```

## Completion criteria

```text
Phase 2 scope is documented
Phase 2 non-scope is documented
Phase 2 guardrails are documented
Phase 2 verification expectations are documented
IMPLEMENTATION_PLAN.md remains unchanged
```

---

# Step 1: Provider Test Doubles

## References

* `docs/03_runtime_loop.md`
* `docs/08_version1_phase1_baseline.md`

## Work

Add a provider test double that can return scripted:

```text
final answers
tool requests
token usage
provider errors
timeouts
malformed responses
budget-relevant usage
```

Keep the live Anthropic/OpenAI provider available for configured local CLI runs.

Use the test double in runtime-loop tests by default.

## Suggested files

```text
runtime/provider_double.py
tests/test_provider_double.py
tests/test_runtime_loop.py
```

## Requirements

The provider test double must support:

```text
scripted response sequence
scripted tool calls
scripted usage values
scripted provider errors
scripted timeout behavior
```

## Tests

Add deterministic runtime-loop tests for:

```text
successful final answer
tool use flow
provider error
provider timeout
budget behavior
malformed provider response
```

## Completion criteria

```text
default pytest does not require provider credentials
runtime-loop tests can simulate provider behavior deterministically
live provider is still available for configured local CLI runs
```

---

# Step 2: Trace Schema Validation

## References

* `docs/05_redaction_trace.md`
* `docs/06_eval_strategy.md`

## Work

Define Pydantic models for existing Phase 1 trace event types.

Validate common fields on every event.

Validate event-specific fields for:

```text
run_started
llm_call
tool_call
run_finished
```

Validate allowed `run_finished.status` values.

Validate UTC ISO 8601 timestamps.

Validate that token and cost fields are present where required.

## Suggested files

```text
runtime/trace_schema.py
tests/test_trace_schema.py
fixtures/traces/
```

## Common event fields

Every trace event should include:

```text
schema_version
run_id
event_type
timestamp
```

Where applicable, events should include:

```text
step
parent_run_id
input_hash
```

## Required event types

```text
run_started
llm_call
tool_call
run_finished
```

## Allowed `run_finished.status`

```text
success
max_steps_exceeded
max_tokens_exceeded
max_cost_exceeded
tool_error
llm_error
validation_error
```

Add `timeout_error` to the trace writer and schema validator enum before timeout traces are emitted.

## Tests

Add trace schema tests using fixture JSONL traces.

Add negative cases for:

```text
missing schema_version
unsupported schema_version
missing common fields
invalid event_type
invalid status value
malformed timestamp
missing token usage on llm_call
missing cost fields where required
unredacted sensitive value if detectable by fixture
```

## Schema version

Phase 2 schema validation must enforce `schema_version`.

## Completion criteria

```text
valid fixture traces pass schema validation
invalid fixture traces fail with clear validation errors
status enum is enforced
timestamps are validated as UTC ISO 8601
```

---

# Step 3: Trace Replay Fixtures

## References

* `docs/03_runtime_loop.md`
* `docs/05_redaction_trace.md`
* `docs/08_version1_phase1_baseline.md`

## Work

Add fixture traces that represent:

```text
successful runs
provider error runs
tool error runs
validation error runs
max step stops
max cost stops
timeout stops
```

Preserve the meaning of `input_hash` as **run-condition tracking**, not deterministic output proof.

Support replay-style checks that compare:

```text
run structure
tool sequence
redaction state
budget fields
terminal status
error metadata
```

## Important definition

Phase 2 replay is **trace replay only**.

It must not:

```text
call live LLMs
re-execute tools
connect to DB
mutate files
```

## Suggested files

```text
fixtures/traces/success_basic.jsonl
fixtures/traces/provider_error.jsonl
fixtures/traces/tool_error.jsonl
fixtures/traces/max_steps_exceeded.jsonl
fixtures/traces/max_cost_exceeded.jsonl
tests/test_trace_replay.py
```

## Tests

Add replay fixture tests that do not call a live LLM.

Verify replay checks can distinguish:

```text
expected tool behavior
malformed traces
missing terminal events
wrong status
unredacted fixture data
```

## Completion criteria

```text
trace replay fixtures exist
trace replay does not call provider or tools
malformed traces are rejected clearly
```

---

# Step 4: Trace Analysis Helpers

## References

* `docs/05_redaction_trace.md`
* `docs/06_eval_strategy.md`

## Work

Add small helpers for reading JSONL trace files and summarizing:

```text
tool calls
final status
token totals
cost totals
error details
limit-stop reasons
final answer summary if present
```

Keep helpers local and file based in Phase 2.

Do not add external observability services.

## Suggested files

```text
runtime/trace_reader.py
runtime/trace_summary.py
tests/test_trace_summary.py
```

## Expected summary fields

```text
run_id
status
event_count
tool_call_count
tools_used
total_input_tokens
total_output_tokens
estimated_total_cost_usd
error_type
error_source
error_message
trace_path
```

## Tests

Add tests for trace summary output using local fixtures.

Verify malformed JSONL fails with a clear validation error.

## Completion criteria

```text
trace summary can be generated from fixture traces
malformed JSONL is handled clearly
summary contains status, tools, tokens, cost, and errors
```

---

# Step 5: Runtime Timeout Handling

## References

* `docs/03_runtime_loop.md`
* `docs/08_version1_phase1_baseline.md`

## Work

Add explicit timeout behavior around provider calls where practical.

Preserve database statement timeout behavior.

Return a clear terminal run status and error message when timeout handling stops a run.

Ensure timeout details are redacted before trace persistence.

## Suggested config

```yaml
runtime:
  provider_timeout_seconds: 60
  tool_timeout_seconds: 60
```

## Expected status

For provider/runtime timeout:

```text
timeout_error
```

## Expected error metadata

```json
{
  "error": {
    "type": "timeout_error",
    "message": "redacted timeout message",
    "retryable": true,
    "source": "provider"
  }
}
```

## Tests

Add timeout tests using provider test doubles.

Verify `run_finished` records:

```text
status = timeout_error
error.type = timeout_error
redacted error message
```

## Completion criteria

```text
provider timeout path is deterministic in tests
timeout stops the run cleanly
run_finished records timeout_error
trace error details are redacted
```

---

# Step 6: Runtime Error Reporting

## References

* `docs/03_runtime_loop.md`
* `docs/05_redaction_trace.md`

## Work

Normalize errors from:

```text
provider calls
tool calls
validation failures
budget stops
timeouts
internal runtime failures
```

Keep final CLI output useful without exposing secrets or raw SQL result PII.

Ensure trace events include enough error metadata to debug failures.

## Required error shape

```json
{
  "error": {
    "type": "provider_error",
    "message": "redacted message",
    "retryable": false,
    "source": "provider"
  }
}
```

## Allowed error.type

```text
provider_error
tool_error
validation_error
timeout_error
budget_error
internal_error
```

## Allowed error.source

```text
provider
tool
runtime
validator
budget
unknown
```

## Tests

Add tests for:

```text
provider error
tool error
validation error
timeout error
budget error
unexpected runtime error
```

Verify error details in traces are redacted.

## Completion criteria

```text
runtime uses normalized error metadata
trace stores redacted error information
CLI output is useful but does not expose secrets
```

---

# Step 7: Limit Reporting Improvements

## References

* `docs/03_runtime_loop.md`
* `docs/05_redaction_trace.md`

## Work

Make the following stops explicit in traces and final output:

```text
max step
max token
max cost
max tool result size
```

Include observed totals and configured limits in redacted metadata where useful.

Preserve post-call token and cost accounting.

## Suggested config

If not already present, add:

```yaml
runtime:
  max_tool_result_rows: 100
  max_tool_result_chars: 20000
```

## Expected statuses

```text
max_steps_exceeded
max_tokens_exceeded
max_cost_exceeded
```

For tool result truncation, do not necessarily stop the run unless configured. Instead, record metadata:

```json
{
  "tool_result_truncated": true,
  "max_tool_result_rows": 100,
  "max_tool_result_chars": 20000
}
```

## Tests

Add tests for:

```text
max step
max token
max cost
tool-result truncation behavior
```

Verify limit metadata is present in `run_finished` or related trace events.

## Completion criteria

```text
limit stops are explicit
limit metadata is visible in trace
tool result truncation is traceable
post-call accounting remains intact
```

---

# Step 8: Expanded Eval Case Coverage

## References

* `docs/06_eval_strategy.md`
* `docs/08_version1_phase1_baseline.md`

## Work

Expand deterministic JSONL eval cases for:

```text
domain questions
SQL safety
response format
expected tool behavior
redaction expectations
path handling expectations
limit-stop expectations
```

Keep eval cases local and reviewable.

Avoid LLM-as-a-judge in Phase 2 default tests.

## Important distinction

```text
Step 8 expands eval datasets.
Step 9 implements trace-based assertions over those cases.
```

## Suggested files

```text
evals/domain_cases.jsonl
evals/sql_safety_cases.jsonl
evals/response_format_cases.jsonl
evals/redaction_cases.jsonl
evals/runtime_limit_cases.jsonl
```

## Tests

Update eval-runner tests to load and validate expanded cases.

Verify required eval fields are present and well typed.

## Completion criteria

```text
expanded eval files exist
eval schema validation passes
default evals do not require live LLM calls
```

---

# Step 9: Trace-Based Eval Assertions

## References

* `docs/06_eval_strategy.md`

## Work

Implement trace-based assertions for eval cases.

Assertions should validate:

```text
partial-order tool-call validation for tools_call_order
forbidden tools are absent
required tools are present
trace redaction invariants
cost fields are present for LLM calls
token fields are present for LLM calls
terminal status matches expectation where configured
```

## `tools_call_order` semantics

`tools_call_order` is a **partial order**.

This means:

```text
specified tools must appear in the specified relative order
other tool calls may appear between them
exact full sequence match is not required
```

## Tests

Add positive and negative tests for:

```text
partial-order validation
duplicate tool calls
forbidden tool detection
missing required tool
redacted tool output samples
missing token/cost fields
wrong terminal status
```

## Completion criteria

```text
trace-based eval assertions work on fixture traces
partial-order validation is implemented
redaction invariants are checked
forbidden tools are detected
```

---

# Step 10: SQL Dialect and CTE Coverage

## References

* `docs/04_tools_sql_security.md`
* `docs/06_eval_strategy.md`

## Work

Expand SQL validation cases across configured parser dialects where supported by `sqlglot`.

Add CTE extraction cases with:

```text
nested subqueries
aliases
JOINs
schema-qualified tables
CTE aliases
physical tables inside CTEs
```

Confirm:

```text
CTE aliases are not misclassified as physical tables
physical tables inside CTEs are still validated
physical tables inside subqueries are still validated
subquery access to disallowed tables is rejected
```

## Important behavior

`extract_tables()` must detect tables inside subqueries.

This is intentional.

Example:

```sql
SELECT *
FROM allowed_table
WHERE id IN (
  SELECT id FROM disallowed_table
)
```

Expected behavior:

```text
disallowed_table is detected
query is rejected if disallowed_table is not in allowed_tables.yml
```

## Tests

Add dialect-specific parser validation tests.

Add CTE and subquery table-extraction regression tests.

## Completion criteria

```text
CTE aliases are handled correctly
JOIN tables are detected
subquery tables are detected
disallowed subquery tables are rejected
dialect-specific tests pass where supported
```

---

# Step 11: Path Traversal Coverage

## References

* `docs/03_runtime_loop.md`
* `docs/08_version1_phase1_baseline.md`

## Work

Expand path traversal edge cases for knowledge reads.

Include cases for:

```text
encoded traversal
absolute paths
parent-directory traversal
symlink escape
extension confusion
valid relative Markdown paths
```

Keep Markdown-only knowledge reads.

## Tests

Add negative tests for:

```text
../ traversal
absolute path outside project
symlink escape
unsupported extension
extension confusion
```

Add positive tests for:

```text
valid relative Markdown paths under knowledge root
valid relative Markdown paths under skills root
valid relative YAML paths under policies/rules if supported
```

## Completion criteria

```text
valid files can be read
invalid paths are rejected
symlink escape is rejected
unsupported extensions are rejected
path validation error messages are clear
```

---

# Step 12: Redaction Regression Coverage

## References

* `docs/05_redaction_trace.md`
* `docs/08_version1_phase1_baseline.md`

## Work

Expand redaction tests for:

```text
column-based SQL redaction
best-effort text redaction
trace persistence redaction
LLM-visible tool-result redaction
error metadata redaction
```

Add trace assertions that raw sensitive values are not persisted.

Add LLM-visible tool-result assertions where provider test doubles make this deterministic.

## Tests

Verify:

```text
PII columns are replaced with [REDACTED]
non-PII values and row structure are preserved
email patterns are redacted
phone patterns are redacted
token-like keys are redacted
connection strings are redacted
trace fixtures and generated traces do not contain known sensitive values
LLM-visible tool outputs are redacted before provider call
```

## Completion criteria

```text
redaction regression tests pass
raw sensitive fixture values are absent from generated traces
LLM-visible tool results are redacted
non-sensitive structure remains useful
```

---

# Step 13: Phase 2 Verification Pass

## References

* `docs/06_eval_strategy.md`
* `docs/08_version1_phase1_baseline.md`

## Work

Audit Phase 2 tests for deterministic default execution.

Run the required verification command.

Record remaining known limitations in the appropriate documentation.

Confirm Phase 1 local CLI behavior remains supported.

## Required verification

```bash
uv run pytest
```

## Additional recommended checks

```bash
uv run python app/main.py eval
uv run python app/main.py trace-summary <fixture_or_generated_trace>
```

## Completion criteria

```text
all Phase 2 steps are implemented and tested
default tests pass without live LLM calls
Phase 1 guardrails remain intact
Phase 1 local CLI behavior remains supported
known limitations are documented
```

---

# Final Acceptance Criteria

Phase 2 is complete when:

```text
uv run pytest passes
default tests require no live LLM credentials
trace schema validation exists
trace replay fixtures exist
trace summary helpers exist
provider test doubles exist
runtime timeout behavior is tested
runtime error reporting is normalized
limit reporting is explicit
expanded eval cases exist
trace-based eval assertions exist
SQL CTE/subquery coverage exists
path traversal coverage exists
redaction regression coverage exists
Phase 1 guardrails remain intact
```

---

# Guardrails to Preserve

Do not regress these Phase 1 guardrails:

```text
no write SQL tools
no unrestricted SQL execution
read-only SQL validation remains parser-backed
allowed_tables validation remains active
redaction happens before LLM input
redaction happens before trace persistence
trace remains JSONL per run
local CLI remains supported
default tests do not require live LLM calls
```

---

# Claude Code / Codex Instruction Template

```text
Read these files first:

1. SPEC.md
2. docs/00_project_overview.md
3. docs/01_architecture_principles.md
4. docs/08_version1_phase1_baseline.md
5. docs/09_phase2_implementation_plan.md

Implement Phase 2 only.

Do not modify IMPLEMENTATION_PLAN.md.
That file is the Phase 1 historical execution-state file.

Phase 2 goal:
Improve trace validation, eval reliability, runtime error handling, timeout handling, provider test doubles, and deterministic safety coverage.

Do not introduce:
- Web UI
- HTTP API
- LangGraph
- vector database
- external search infrastructure
- multi-agent orchestration
- write SQL tools
- unrestricted SQL execution
- production mutations

Implementation policy:
- Use provider test doubles for default tests.
- Default pytest must not require live LLM credentials.
- Keep trace data redacted.
- Keep SQL validation parser-backed and allowlist-based.
- Keep changes small and explicit.
- Run uv run pytest before declaring done.

Follow docs/09_phase2_implementation_plan.md step by step.
```
