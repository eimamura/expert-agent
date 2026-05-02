# expert-agent

Local-first domain expert AI agent MVP.

This repository implements the Phase 1 version of a single-agent, Markdown-centered expert assistant. It runs from a local CLI, loads curated Markdown knowledge, uses parser-validated read-only SQL tools, redacts sensitive data before LLM input and trace persistence, and writes JSONL traces for each run.

## Project Status

Phase 1 is the current target and is marked complete in `IMPLEMENTATION_PLAN.md`.

Phase 1 includes:

- local CLI execution;
- a single custom agent loop;
- Markdown knowledge, skill, and policy files;
- read-only SQL validation and execution wrappers;
- redaction for text, SQL results, and traces;
- JSONL trace writing;
- pytest-backed eval and safety checks.

Phase 1 intentionally excludes Web UI, HTTP API, LangGraph, multi-agent orchestration, vector search, write tools, and production mutations.

## Read Order

Before making implementation changes, read these files in order:

1. `SPEC.md`
2. `docs/00_project_overview.md`
3. `docs/01_architecture_principles.md`
4. `docs/02_phase1_mvp_scope.md`
5. `IMPLEMENTATION_PLAN.md`

Then read the topic-specific `docs/*.md` file for the area being changed. `CLAUDE.md` contains the repository guardrails for AI coding agents.

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

Set `ANTHROPIC_API_KEY` before running the CLI. If SQL tools are needed, set `DATABASE_URL` for a read-only database connection.

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

## Test

Run the full test suite:

```bash
uv run pytest
```

The tests cover config validation, knowledge loading, redaction, SQL safety, SQL wrappers, trace writing, response formatting, and JSONL eval case shape.

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
```

## Safety Notes

- Use read-only database credentials.
- Only parser-validated single-statement `SELECT` queries are allowed.
- Keep redaction before LLM input and before trace persistence.
- Do not add write SQL tools or an unrestricted SQL execution function.
- Keep Phase 1 local-first and single-agent unless the project phase explicitly changes.
