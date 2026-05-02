# Archived Long Specification v3.3

This file is an English-only archive summary of the previous single-file specification.

Do not use this file as an implementation source. Use these active files instead:

- `../SPEC.md`
- `../IMPLEMENTATION_PLAN.md`
- `../docs/00_project_overview.md`
- `../docs/01_architecture_principles.md`
- `../docs/02_phase1_mvp_scope.md`
- `../docs/03_runtime_loop.md`
- `../docs/04_tools_sql_security.md`
- `../docs/05_redaction_trace.md`
- `../docs/06_eval_strategy.md`
- `../docs/07_future_scaling.md`

## Original role

The previous long specification combined three responsibilities:

1. Design philosophy.
2. Implementation specification.
3. Work instructions for AI coding agents.

The current repository separates those responsibilities into an entry file, detailed topic documents, a Phase 1 implementation plan, and agent guardrails.

## Preserved design intent

The project builds a local-first domain expert AI agent MVP.

The MVP starts with:

- Markdown-centered knowledge;
- a single agent;
- a custom minimal agent loop;
- read-only tools;
- parser-backed SQL safety;
- redaction before LLM input;
- redaction before trace persistence;
- JSONL trace files;
- basic pytest-backed evals;
- local CLI execution.

The MVP intentionally does not start with:

- LangGraph;
- multi-agent orchestration;
- Web UI;
- HTTP API;
- vector DB;
- external search infrastructure;
- write SQL tools;
- production mutation.

## Preserved roadmap

```text
Phase 0: Markdown design and expected-question mapping
Phase 1: Local minimal agent loop
Phase 2: Trace, eval, and runtime refinement
Phase 3: Web/API layer
Phase 4: External search infrastructure
Phase 5: LangGraph / workflow orchestration
Phase 6: Multiple channels
Phase 7: Agent platform
```

## Preserved Phase 1 requirements

Phase 1 must provide:

- local CLI execution;
- one agent;
- direct provider SDK calls;
- a minimal loop;
- Markdown knowledge indexing;
- `read_knowledge_file()`;
- path traversal protection;
- read-only SQL execution;
- SQL dialect configuration;
- parser-backed SELECT-only validation;
- destructive SQL rejection;
- allowed table validation;
- CTE-aware table extraction;
- SQL redaction before LLM input;
- trace redaction before persistence;
- `input_hash`;
- ULID `run_id`;
- max step, token, and cost limits;
- required final response sections;
- pytest coverage for safety behavior.

## Preserved technical decisions

- Python 3.10+.
- `uv` or `poetry` with a committed lock file.
- `sqlglot>=25.0`.
- YAML configuration.
- JSONL trace files.
- ULID run identifiers.
- SQLite as a local MVP database target.

## Preserved safety decisions

- Read-only DB credentials are the primary defense.
- SQL parser validation is defense in depth.
- Phase 1 rejects schema-less table references.
- PII columns are redacted by exact key match.
- Regex text redaction is best-effort.
- Raw SQL results must not be sent to the LLM when they contain unredacted sensitive fields.
- Raw sensitive data must not be written to trace files.

## Current archive policy

This archive is kept only for historical context.
It is excluded from agent context loading through ignore files.
If the active specification conflicts with this archive, the active specification wins.

