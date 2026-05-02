# expert-agent

Local-first domain expert AI agent MVP.

This repository implements a local-first, single-agent, Markdown-centered expert assistant. It runs from a local CLI, loads curated Markdown knowledge, uses parser-validated read-only SQL tools, redacts sensitive data before LLM input and trace persistence, and writes JSONL traces for each run.

## Project Status

Phase 1 is complete in `docs/phase_plans/phase1_implementation_plan.md`.
Phase 2 is complete in `docs/phase_plans/phase2_implementation_plan.md`.
See `docs/baselines/version1_phase1_baseline.md` for the Version 1 Phase 1 comparison baseline.

The current baseline includes:

- local CLI execution;
- a single custom agent loop;
- Markdown knowledge, skill, and policy files;
- read-only SQL validation and execution wrappers;
- redaction for text, SQL results, and traces;
- JSONL trace writing;
- pytest-backed eval and safety checks;
- deterministic provider test doubles for runtime tests;
- Pydantic trace schema validation;
- local trace replay and summary helpers;
- normalized runtime error metadata;
- explicit provider/tool timeout handling;
- trace-based eval assertions and expanded safety coverage.

The current scope intentionally excludes Web UI, HTTP API, LangGraph, multi-agent orchestration, vector search, write tools, unrestricted SQL execution, and production mutations.

## Read Order

Before making implementation changes, read these files in order:

1. `SPEC.md`
2. `docs/00_project_overview.md`
3. `docs/01_architecture_principles.md`
4. `docs/baselines/README.md`
5. `docs/phase_plans/README.md`

Read `docs/baselines/version1_phase1_baseline.md` when you need the Version 1 Phase 1 comparison snapshot. Read `docs/phase_plans/phase1_implementation_plan.md` when you need Phase 1 history, and `docs/phase_plans/phase2_implementation_plan.md` when you need the Phase 2 completion summary. Do not add Phase 2 or later work to the Phase 1 history file. Then read the topic-specific `docs/*.md` file for the area being changed. `CLAUDE.md` contains the repository guardrails for AI coding agents.

## Requirements

- Python 3.10+
- `uv`
- `sqlite3` CLI for inspecting the optional local SQLite database
- Anthropic API key for real agent runs
- Optional local database configured through `DATABASE_URL`

Install dependencies:

```bash
uv sync
```

Create local environment values:

```bash
cp .env.example .env
```

Set `ANTHROPIC_API_KEY` in `.env` before running the CLI. The CLI automatically loads `.env` and uses `DATABASE_URL` from that file when SQL tools are needed.

Create the optional local SQLite seed database:

```bash
uv run python scripts/create_local_sqlite.py
```

This creates `data/local.sqlite`, matching the `DATABASE_URL=sqlite:///./data/local.sqlite` value in `.env.example`. Re-run with `--force` only when you intentionally want to replace the local seed database.

Confirm the seed database has data:

```bash
sqlite3 data/local.sqlite ".tables"
sqlite3 data/local.sqlite "SELECT 'customers', COUNT(*) FROM customers UNION ALL SELECT 'orders', COUNT(*) FROM orders UNION ALL SELECT 'order_items', COUNT(*) FROM order_items UNION ALL SELECT 'products', COUNT(*) FROM products;"
```

## Run

Run the local expert agent:

```bash
uv run python -m app.main "What should I investigate first?"
```

Use a custom config file:

```bash
uv run python -m app.main --config config/app.yml "Summarize the available KPI definitions."
```

Runtime settings live in `config/app.yml`, including model aliases, limits, database dialect, domain root, knowledge read-size limit, trace directory, and pricing.
Domain assets live under the configured domain pack root, currently `domains/subscription_commerce/`; Markdown knowledge is loaded from that root's `knowledge/` directory.

Run deterministic local eval validation:

```bash
uv run python app/main.py eval
```

Summarize a JSONL trace:

```bash
uv run python app/main.py trace-summary fixtures/traces/success_basic.jsonl
```

## Test

Run the full test suite:

```bash
uv run pytest
```

The tests cover config validation, knowledge loading, redaction, SQL safety, SQL wrappers, runtime loop behavior with provider doubles, trace writing, trace schema validation, trace replay, trace summaries, trace-based eval assertions, response formatting, and JSONL eval case shape.

## Repository Layout

```text
agents/     Prompt contract and agent-facing instructions
app/        CLI entry point
config/     Runtime configuration
domains/    Domain packs with knowledge, skills, policies, rules, and evals
docs/       Detailed project specification by topic
runtime/    Agent loop, state, config, tracing, hashing, cost, redaction
scripts/    Local developer setup utilities
tests/      Pytest suite
tools/      Read-only tool implementations
traces/     Per-run JSONL trace output
fixtures/   Redacted trace fixtures for schema, replay, and summary tests
```

## Safety Notes

- Use read-only database credentials.
- Only parser-validated single-statement `SELECT` queries are allowed.
- Keep redaction before LLM input and before trace persistence.
- Do not add write SQL tools or an unrestricted SQL execution function.
- Keep the runtime local-first and single-agent unless a later project phase explicitly changes it.
