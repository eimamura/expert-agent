# docs/04_tools_sql_security.md

## Role

This document defines the SQL tool and database-safety specification.

## Read first

- `../SPEC.md`
- `docs/02_phase1_mvp_scope.md`
- `docs/03_runtime_loop.md`

## Related documents

- `docs/05_redaction_trace.md`
- `docs/06_eval_strategy.md`

## Implementation targets

- `tools/sql.py`
- `domains/subscription_commerce/rules/allowed_tables.yml`
- `domains/subscription_commerce/rules/pii_columns.yml`
- `tests/test_sql_safety.py`
- `tests/test_tools.py`

---

# SQL Tool and DB Safety

## Required tool API

`tools/sql.py` should expose safe wrappers such as:

```python
def list_tables() -> list[str]:
    ...

def get_table_schema(table_name: str) -> dict:
    ...

class SqlToolResult(TypedDict):
    rows: list[dict]
    redacted_columns: list[str]
    row_count: int
    truncated: bool
    metadata: dict

def run_readonly_sql(query: str) -> SqlToolResult:
    ...
```

`run_readonly_sql()` must return redacted rows and metadata, not raw database rows.

## Primary safety requirement

The database credential must be read-only.

Required DB posture:

- grant SELECT only;
- do not use credentials with write permissions;
- do not connect to production with mutation-capable credentials.

Tool-side SQL validation is a defense-in-depth layer. DB permissions are the primary protection.

## SQL dialect

The SQL dialect is configured in `config/app.yml`:

```yaml
database:
  dialect: "sqlite"
```

Supported initial candidates:

- `sqlite`
- `postgres`
- `mysql`
- `tsql`
- `databricks`

The implementation must pass the configured dialect to `sqlglot`.

## Allowed tables

`domains/subscription_commerce/rules/allowed_tables.yml` should list fully qualified physical tables.

Example:

```yaml
allowed_tables:
  - main.customers
  - main.orders
  - main.order_items
```

Phase 1 rejects schema-less table references. This avoids dialect-dependent default schema behavior.

## SQL validation

`validate_readonly_sql(query: str, dialect: str, allowed_tables: set[str])` must:

- parse the query with `sqlglot`;
- require exactly one statement;
- require the top-level statement to be SELECT-like;
- reject INSERT, UPDATE, DELETE, MERGE, DROP, CREATE, ALTER, TRUNCATE, and command statements anywhere in the AST;
- reject multiple statements;
- reject comments or syntax forms that hide extra statements;
- reject table references not present in `allowed_tables`;
- reject schema-less table references in Phase 1;
- allow safe CTEs;
- not treat CTE names as physical tables.

## Destructive node detection

Validation must walk the parsed AST and reject destructive expression types, including:

- `Insert`
- `Update`
- `Delete`
- `Merge`
- `Drop`
- `Create`
- `Alter`
- `TruncateTable`
- `Command`

Use the `sqlglot>=25.0` API assumption that `Expression.walk()` yields expressions directly.

## Subqueries and CTEs

Table extraction must inspect nested queries and subqueries.

Expected behavior:

- physical tables inside subqueries are validated;
- CTE names are excluded from physical table validation;
- physical tables referenced inside CTE definitions are validated;
- writes hidden inside CTEs are rejected.

## `extract_tables()` behavior

Required behavior:

- return physical table references only;
- normalize table names to the configured representation;
- include schema and table name;
- reject omitted schema in Phase 1;
- avoid returning CTE aliases;
- inspect subqueries.

Example:

```sql
WITH recent_orders AS (
  SELECT * FROM main.orders
)
SELECT * FROM recent_orders
```

Expected extracted physical table:

```text
main.orders
```

`recent_orders` must not be returned as a physical table.

## Forbidden SQL examples

These must be rejected:

```sql
DELETE FROM main.orders
```

```sql
UPDATE main.customers SET email = 'x'
```

```sql
SELECT * FROM main.orders; DROP TABLE main.orders;
```

```sql
WITH deleted AS (
  DELETE FROM main.orders RETURNING *
)
SELECT * FROM deleted
```

```sql
SELECT * FROM orders
```

The last example is rejected because the schema is omitted in Phase 1.

## Allowed SQL examples

These may be allowed when referenced tables are approved:

```sql
SELECT COUNT(*) FROM main.orders
```

```sql
WITH recent_orders AS (
  SELECT * FROM main.orders WHERE created_at >= '2026-01-01'
)
SELECT COUNT(*) FROM recent_orders
```

## Execution wrapper

`run_readonly_sql()` must:

- validate SQL before execution;
- use read-only credentials;
- apply statement timeout if supported;
- limit returned rows;
- limit serialized result bytes;
- redact rows before returning data to the LLM;
- record useful metadata for trace events.

## Security requirements

Required from the MVP:

- Use read-only DB credentials.
- Validate SQL with a parser.
- Reject write operations.
- Restrict tables through `allowed_tables.yml`.
- Redact PII columns.
- Truncate oversized results.
- Trace tool calls after redaction.

## Production DB policy

Phase 1 does not perform production updates.

If production read access is needed later:

- use a read-only account;
- use network and credential isolation;
- prefer replicas or read-only endpoints;
- keep write credentials out of the agent runtime.
