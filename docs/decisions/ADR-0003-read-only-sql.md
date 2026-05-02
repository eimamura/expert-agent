# ADR-0003: Read-Only SQL Tools Only

## Status

Accepted

## Context

The agent needs to inspect database content to answer questions about subscription commerce data. The question was whether to give it general database access or constrain it to read operations only.

## Decision

The agent may only execute SELECT-like SQL. Write, update, delete, and DDL operations are permanently out of scope. There is no `execute_any_sql` tool and there will never be one in this project.

## Rationale

This agent answers questions — it does not manage data. Giving it write access would:

- Risk accidental or prompt-injection-driven data corruption
- Require significantly more complex authorization and audit logic
- Contradict the "start read-only, expand deliberately" principle

The layered safety controls are:

1. Read-only database credentials at the connection level
2. Parser-backed SQL validation (`sqlglot`) that rejects non-SELECT AST nodes
3. Allowlisted schema-qualified table names from `allowed_tables.yml`
4. Column-level PII redaction before results reach the LLM
5. Regex redaction before trace persistence

All five layers must remain intact. Removing any one of them requires a formal decision.

## Consequences

**Positive**

- Production databases are safe to connect to read-only replicas.
- SQL injection attempts cannot cause writes.
- Audit surface is small and testable.

**Negative**

- The agent cannot be extended to perform automated data entry or corrections without a new ADR.

## References

- `tools/sql.py` — SQL execution wrapper
- `docs/04_tools_sql_security.md` — SQL tool security spec
- `domains/subscription_commerce/rules/allowed_tables.yml` — allowlist
- `domains/subscription_commerce/rules/pii_columns.yml` — column redaction config
