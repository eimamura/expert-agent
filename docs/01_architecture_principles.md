# docs/01_architecture_principles.md

## Role

This document defines the core architecture principles: local-first, single-agent, Markdown-centered, and read-only tooling.

## Read first

- `../SPEC.md`
- `docs/00_project_overview.md`

## Related documents

- `docs/02_phase1_mvp_scope.md`
- `docs/07_future_scaling.md`

---

# Architecture Principles

## Non-negotiable MVP principles

```text
Start local-first.
Start with one agent.
Start with Markdown-centered knowledge.
Start with a minimal custom agent loop.
Start with read-only tools.
Do not update production systems.
Do not build a complex UI first.
Do not require LangGraph in Phase 1.
```

## Design intent

The MVP is not a platform rewrite. It is a controlled local implementation that proves whether a domain expert agent can:

- load curated knowledge;
- inspect approved Markdown files;
- execute safe read-only SQL;
- redact sensitive output;
- produce traceable answers;
- run basic evals;
- stay small enough to debug.

## Why not start with LangGraph

LangGraph and workflow engines are useful later, but Phase 1 should prioritize:

- clear control flow;
- debuggable tool execution;
- explicit trace records;
- simple state transitions;
- low implementation overhead.

Phase 5 can introduce LangGraph once the runtime behavior is proven.

## Why Markdown first

Markdown is the right starting format because:

- humans can edit it directly;
- agents can read it without custom infrastructure;
- Git diffs are useful;
- it keeps knowledge curation independent from retrieval infrastructure.

External search or vector databases are Phase 4 concerns.

## Why read-only tools first

The first useful version should answer questions, inspect data, and provide evidence. It should not mutate production systems.

The primary protections are:

- read-only DB credentials;
- parser-backed SQL validation;
- allowed table configuration;
- redaction before LLM input;
- redaction before trace persistence;
- tests for unsafe behavior.

## Context loading strategy

Agents should load context in this order:

1. `SPEC.md`
2. `docs/00_project_overview.md`
3. `docs/01_architecture_principles.md`
4. `docs/02_phase1_mvp_scope.md`
5. `IMPLEMENTATION_PLAN.md`
6. Topic-specific documents for the current step

Stable context should be loaded before mutable execution state. This separation also helps prompt caching because architecture documents change less often than the implementation plan.

## Phase boundaries

Phase 1 implements only:

- local CLI execution;
- a single agent;
- a minimal loop;
- Markdown knowledge loading;
- read-only SQL tools;
- redaction;
- JSONL trace;
- basic pytest-backed evals.

Phase 1 must not implement:

- Web UI;
- HTTP API;
- LangGraph;
- multi-agent orchestration;
- vector search;
- write tools;
- production mutation.

