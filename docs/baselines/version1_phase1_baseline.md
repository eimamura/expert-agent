# docs/baselines/version1_phase1_baseline.md

## Purpose

Version 1 records the completed Phase 1 MVP: a local-first domain expert agent that can answer subscription commerce questions from curated Markdown knowledge and safe read-only database inspection.

Phase 1 exists to prove the smallest useful runtime before adding service layers, search infrastructure, workflow orchestration, or production integrations. It is a comparison baseline for Phase 2, not a replacement for the detailed Phase 1 specifications in the earlier `docs/*.md` files.

## Implemented Capabilities

- Local CLI entry point through `app/main.py`.
- Simple `.env` auto-load before config loading, currently used for `ANTHROPIC_API_KEY` and `DATABASE_URL`.
- YAML runtime config in `config/app.yml`, including model alias resolution, limits, database dialect, domain root, knowledge limits, trace settings, and pricing.
- Domain pack loading from `domains/subscription_commerce/`.
- Markdown knowledge indexing from the domain pack `knowledge/` directory.
- `read_knowledge_file` tool with Markdown-only reads, absolute-path rejection, path traversal protection, and file-size enforcement.
- Minimal custom agent loop in `runtime/loop.py`.
- Direct Anthropic provider implementation with tool-calling support.
- Tool schemas for `read_knowledge_file`, `list_tables`, `get_table_schema`, and `run_readonly_sql`.
- Parser-backed read-only SQL validation with `sqlglot`.
- Allowlisted schema-qualified physical tables from `domains/subscription_commerce/rules/allowed_tables.yml`.
- SQLite execution wrapper for local read-only SQL inspection.
- Local SQLite seed database script at `scripts/create_local_sqlite.py`.
- `sqlite3` inspection workflow documented in `README.md`.
- Column-based SQL result redaction using `pii_columns.yml`.
- Regex-based best-effort text redaction using `redaction.yml`.
- Redaction before tool results are added to LLM-visible state.
- Redaction before trace event persistence.
- JSONL trace files in `traces/{run_id}.jsonl`.
- ULID run IDs and Phase 1 `parent_run_id` emitted as null.
- `input_hash` derived from run conditions, including the question, prompt template, knowledge file hashes, config snapshot, tool schema identifiers, allowed tables, redaction config, provider, and concrete model id.
- Post-call token and cost accounting.
- Limits for steps, total tokens, per-call output tokens, total run cost, and tool result size.
- Final response formatting for required answer sections.
- Pytest coverage for config, CLI `.env` loading, knowledge loading, path safety, SQL validation, SQL wrappers, redaction, trace writing, response formatting, eval case shape, and local SQLite seed creation.

## Runtime Behavior

1. The CLI parses the question and optional `--config` path.
2. The CLI loads `.env` values into missing environment variables.
3. Runtime config is loaded and validated from YAML.
4. The configured model alias is resolved to a concrete provider model id for the runtime snapshot.
5. The configured domain root is used to derive knowledge and rules paths.
6. Markdown files under the domain pack `knowledge/` directory are listed, previewed, hashed, and rendered into a compact knowledge index.
7. The run creates a ULID `run_id`, null `parent_run_id`, config snapshot, and `input_hash`.
8. A `run_started` trace event is written after redaction.
9. The system prompt is rendered from `SYSTEM_PROMPT_TEMPLATE` and the knowledge index.
10. The LLM is called through the Anthropic provider with the configured model, temperature, output-token limit, conversation messages, and tool schemas.
11. Token usage and estimated cost are accumulated after each provider response.
12. Each LLM call writes a redacted `llm_call` trace event with token and cost fields.
13. If the LLM requests tools, the loop executes the supported local tool by name.
14. Knowledge tool calls read only safe relative Markdown paths beneath the knowledge root.
15. SQL tool calls validate SQL before execution, require approved schema-qualified tables, execute only through the SQLite wrapper in Phase 1, limit results, and redact PII columns.
16. Tool results are truncated when they exceed configured size limits.
17. Tool output is redacted, traced, and appended back to the LLM-visible conversation as a tool result.
18. The loop continues until a final answer, max steps, max tokens, max cost, tool error, or LLM error.
19. The final answer is normalized to include the required response sections when the model omits them.
20. A `run_finished` trace event records status, steps, total tokens, total cost, and error details.

## Safety and Guardrails

- SQL execution is read-only by design and should use read-only database credentials.
- The SQLite connection opens local databases with `mode=ro`.
- SQL validation uses a parser and requires exactly one SELECT-like statement.
- Destructive SQL AST nodes are rejected.
- Multiple statements are rejected.
- Schema-less table references are rejected in Phase 1.
- Physical table references must be listed in `allowed_tables.yml`.
- CTE names are not treated as physical tables, while physical tables inside CTE definitions and subqueries are still validated.
- SQL result PII is redacted by exact column-name match before returning rows to the agent loop.
- Text fields in trace events are passed through configured redaction patterns before persistence.
- Tool results are redacted before they are visible to the LLM.
- No write SQL tools exist.
- There is no unrestricted `execute_any_sql` tool.
- Phase 1 does not mutate production systems.

## Known Limitations

- The runtime is a single agent.
- The interface is local CLI only.
- There is no Web UI.
- There is no HTTP API.
- LangGraph is not used.
- There is no multi-agent orchestration.
- There is no vector database or external search infrastructure.
- Markdown retrieval is naive: files are listed and summarized, then explicitly read by tool call.
- The only implemented live provider wrapper is Anthropic.
- SQL execution currently supports SQLite only, although config validation recognizes several dialect names for parser validation.
- The `.env` parser is intentionally simple and does not implement full shell-compatible dotenv semantics.
- Provider calls do not have an explicit timeout wrapper.
- Traces are local JSONL files with one file per run.
- Trace storage is not date-partitioned and is not externalized.
- `memory/` exists as an unused placeholder.
- `input_hash` tracks run conditions and does not guarantee deterministic LLM output.
- Regex text redaction is best-effort and may miss sensitive data.

## Version 1 Baseline for Phase 2 Comparison

Phase 2 should preserve:

- Local-first execution as a supported workflow.
- The single-run trace contract with redaction before persistence.
- Redaction before LLM-visible tool results.
- Parser-backed read-only SQL validation.
- Allowlisted schema-qualified table access.
- No write tools and no production mutation by default.
- `input_hash` as a run-condition identifier.
- Required final-answer sections.
- Deterministic pytest coverage that does not require live LLM calls by default.

Phase 2 may improve:

- Trace structure, validation, replay, and analysis.
- Eval coverage and trace-based assertions.
- Runtime error handling and timeout behavior.
- Provider abstraction and provider test doubles.
- Cost, token, and tool-result limit reporting.
- Markdown retrieval quality while keeping curated Markdown as a supported source.
- Developer workflows around local SQLite setup and inspection.

Phase 2 may replace later:

- The naive Markdown retrieval strategy.
- Local JSONL-only trace storage.
- The direct custom loop if a later phase explicitly introduces a workflow engine.
- SQLite-only execution when a production-safe read-only database target is introduced.
