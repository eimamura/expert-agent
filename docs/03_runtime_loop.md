# docs/03_runtime_loop.md

## Role

This document defines the Phase 1 agent loop, runtime config, model alias handling, run IDs, token/cost limits, input hashing, and Markdown loading.

## Read first

- `../SPEC.md`
- `docs/02_phase1_mvp_scope.md`

## Related documents

- `docs/04_tools_sql_security.md`
- `docs/05_redaction_trace.md`

## Implementation targets

- `app/main.py`
- `agents/prompts.py`
- `runtime/loop.py`
- `runtime/state.py`
- `runtime/config.py`
- `runtime/cost.py`
- `runtime/hashing.py`
- `runtime/ids.py`
- `runtime/knowledge_loader.py`
- `config/app.yml`

---

# Runtime Loop

## Config file

`config/app.yml` should contain runtime, model, database, domain, knowledge, trace, and pricing settings.

Example:

```yaml
runtime:
  max_steps: 8
  max_total_tokens: 120000
  max_output_tokens_per_call: 4096
  max_run_cost_usd: 3.0
  max_tool_result_bytes: 20000

llm:
  provider: "anthropic"
  model_id: "claude-sonnet-4-5"
  temperature: 0

database:
  url_env: "DATABASE_URL"
  dialect: "sqlite"
  statement_timeout_seconds: 30

domain:
  root: "domains/subscription_commerce"

knowledge:
  max_file_read_bytes: 200000

trace:
  dir: "traces"
  output_sample_size: 5
  output_sample_strategy: "head"

pricing:
  claude-sonnet-4-5:
    input_per_million_usd: 3.0
    output_per_million_usd: 15.0
```

## Model alias policy

Development may use a model alias such as `sonnet_latest`, but production config snapshots must contain the resolved concrete `model_id`.

Pricing lookup order:

1. concrete `model_id`;
2. model alias, only when the concrete id is not present.

`config_snapshot.llm.model_id` must contain the resolved concrete id. Do not store the alias itself in the runtime snapshot used for replay comparisons.

## `runtime/ids.py`

Use ULID for `run_id` values.

Requirements:

- `run_id` is unique enough for local traces.
- `run_id` is time-sortable.
- ULID package usage is isolated in `runtime/ids.py` so it can be replaced later.

Example API:

```python
def new_run_id() -> str:
    ...
```

## Minimal loop behavior

`runtime/loop.py` owns the core loop.

Expected sequence:

1. Build initial state.
2. Build the system prompt from `SYSTEM_PROMPT_TEMPLATE`, domain skills and policies, and the knowledge index.
3. Call the LLM.
4. If the LLM requests a tool, validate and execute the tool.
5. Redact tool output before appending it to LLM-visible state.
6. Save redacted trace events.
7. Call the LLM again.
8. Stop on final answer, max step, max token, max cost, or error.

The loop should be deliberately small and explicit. Do not introduce LangGraph in Phase 1.

## State

`runtime/state.py` should hold the runtime state needed by the loop:

- `run_id`
- `parent_run_id`
- messages or provider-compatible conversation state
- executed tool calls
- accumulated token usage
- accumulated cost
- current step count
- `input_hash`
- config snapshot
- final status

## Token and cost limits

Phase 1 uses post-call accounting. This means usage is accumulated after each LLM response because provider usage is only known after the call returns.

Required limits:

- `runtime.max_steps`
- `runtime.max_total_tokens`
- `runtime.max_output_tokens_per_call`
- `runtime.max_run_cost_usd`
- `runtime.max_tool_result_bytes`

If a limit is exceeded after a call, the run should stop with a defined `run_finished.status`.

## `runtime/cost.py`

Required behavior:

- Read model pricing from config.
- Calculate cost from input and output token counts.
- Accumulate per-run cost.
- Resolve pricing by concrete model id first.
- Support aliases only as a development convenience.

Example API:

```python
def estimate_call_cost_usd(
    model_id: str,
    input_tokens: int,
    output_tokens: int,
    pricing: dict,
) -> float:
    ...
```

## Prompt contract

`agents/prompts.py` must export:

```python
SYSTEM_PROMPT_TEMPLATE: str
```

Rules:

- The Phase 1 system prompt must be in English.
- `{DOMAIN_INSTRUCTIONS}` must appear exactly once.
- `{KNOWLEDGE_INDEX}` must appear exactly once.
- Do not inject dynamic data through other ad hoc placeholders.
- The template body is part of `input_hash`.
- The rendered knowledge index is accounted for separately through knowledge file hashes.
- The rendered domain instructions are accounted for separately through skills and policies file hashes.

The prompt must tell the agent:

- use tools when evidence is needed;
- follow injected domain skills and policies;
- do not invent table names;
- do not use redacted values for value-level analysis;
- include evidence and uncertainty;
- respect the response format.

## `input_hash`

`input_hash` identifies run conditions. It does not guarantee identical LLM output.

It should include:

- user question;
- system prompt template;
- knowledge file paths and content hashes;
- domain instruction file paths and content hashes from `skills/*.md` and `policies/*.md`;
- relevant config snapshot;
- tool schema identifiers;
- allowed table configuration hash;
- redaction configuration hash;
- model provider and concrete model id.

It should not include:

- rendered provider response text;
- timestamps;
- generated `run_id`;
- trace file path;
- non-deterministic provider metadata.

Use stable JSON serialization with sorted keys before hashing.

## `runtime/hashing.py`

Required APIs:

```python
def stable_json_dumps(value: object) -> str:
    ...

def sha256_text(value: str) -> str:
    ...

def compute_input_hash(parts: dict) -> str:
    ...
```

## Markdown loading

Phase 1 uses naive retrieval:

- list available Markdown files;
- include a short index in the system prompt;
- let the agent call `read_knowledge_file(path)` for full content.
- derive the knowledge directory from `domain.root / "knowledge"`.

No vector DB is used in Phase 1.

Domain pack instructions are loaded separately from retrievable knowledge:

- read `domain.root / "skills"/*.md` and `domain.root / "policies"/*.md`;
- include only `.md` files;
- treat missing `skills/` or `policies/` directories as empty;
- load in deterministic order: all skills first, then all policies, with filenames sorted ascending within each directory;
- inject the full rendered content into the system prompt under explicit `## Domain Skills` and `## Domain Policies` sections.

## `runtime/knowledge_loader.py`

Required APIs:

```python
class KnowledgeFileInfo(TypedDict):
    path: str
    preview: str
    bytes: int
    sha256: str

def list_knowledge_files(root: Path) -> list[KnowledgeFileInfo]:
    ...

def read_knowledge_file(root: Path, requested_path: str, max_bytes: int) -> str:
    ...
```

## Path security requirements

`read_knowledge_file()` must:

- reject absolute paths;
- normalize the requested path;
- reject `..` traversal;
- ensure the resolved path is under the derived knowledge directory;
- read only Markdown files unless explicitly extended later;
- enforce `knowledge.max_file_read_bytes`;
- return a clear error for missing files.

Use structured path APIs instead of string prefix checks.
