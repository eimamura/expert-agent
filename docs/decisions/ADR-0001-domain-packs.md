# ADR-0001: Use Domain Packs for Business Logic

## Status

Accepted

## Context

This project will eventually serve multiple distinct business domains (e.g., subscription commerce, manufacturing). If domain-specific knowledge, rules, and policies are mixed into shared infrastructure, the agent's context window becomes polluted with irrelevant information, increasing hallucination risk. It also makes onboarding a new domain harder.

## Decision

Adopt a `domains/[domain_name]/` directory structure. Each domain pack encapsulates its own:

- `knowledge/` — curated Markdown files the agent can read
- `rules/` — allowed tables, redaction config, policies
- `evals/` — domain-specific eval cases

The `app/` directory contains only shared infrastructure (runtime loop, providers, tools, trace). It calls into domain packs via config; it does not embed domain knowledge directly.

## Consequences

**Positive**

- The agent's context window can be restricted to the active domain at runtime.
- Adding a new domain does not require touching shared infrastructure.
- Domain knowledge can be updated independently of the runtime.

**Negative**

- A light convention is needed so `app/` knows how to load any domain pack.
- Integration tests must cover the domain-loading path.

## References

- `domains/subscription_commerce/` — first implemented domain pack
- `docs/00_project_overview.md` — overall project structure
