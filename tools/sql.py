from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any, TypedDict

import sqlglot
from sqlglot import exp

from runtime.config import load_allowed_tables, load_config, load_pii_columns
from runtime.redaction import redact_sql_rows


class SqlToolResult(TypedDict):
    rows: list[dict[str, Any]]
    redacted_columns: list[str]
    row_count: int
    truncated: bool
    metadata: dict[str, Any]


DESTRUCTIVE_EXPRESSIONS = (
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Merge,
    exp.Drop,
    exp.Create,
    exp.Alter,
    exp.TruncateTable,
    exp.Command,
)


def _parse_one_statement(query: str, dialect: str) -> exp.Expression:
    statements = sqlglot.parse(query, read=dialect)
    if len(statements) != 1:
        raise ValueError("SQL must contain exactly one statement")
    statement = statements[0]
    if statement is None:
        raise ValueError("SQL statement is empty")
    return statement


def _cte_names(statement: exp.Expression) -> set[str]:
    names: set[str] = set()
    for cte in statement.find_all(exp.CTE):
        alias = cte.alias
        if alias:
            names.add(alias.lower())
    return names


def _normalized_table(table: exp.Table) -> str:
    name = table.name
    db = table.args.get("db")
    if db is None:
        raise ValueError(f"Schema-less table reference is not allowed: {name}")
    schema = str(db)
    return f"{schema}.{name}"


def extract_tables(query: str, dialect: str) -> set[str]:
    statement = _parse_one_statement(query, dialect)
    cte_names = _cte_names(statement)
    tables: set[str] = set()
    for table in statement.find_all(exp.Table):
        if table.name.lower() in cte_names and table.args.get("db") is None:
            continue
        tables.add(_normalized_table(table))
    return tables


def validate_readonly_sql(query: str, dialect: str, allowed_tables: set[str]) -> None:
    statement = _parse_one_statement(query, dialect)
    if not isinstance(statement, (exp.Select, exp.Union)):
        raise ValueError("Only SELECT-like statements are allowed")
    for node in statement.walk():
        if isinstance(node, DESTRUCTIVE_EXPRESSIONS):
            raise ValueError(f"Forbidden SQL expression: {node.__class__.__name__}")
    referenced = extract_tables(query, dialect)
    disallowed = referenced - allowed_tables
    if disallowed:
        raise ValueError(f"SQL references unapproved tables: {sorted(disallowed)}")


def _sqlite_path_from_url(url: str) -> str:
    if url.startswith("sqlite:///"):
        return url.removeprefix("sqlite:///")
    if url.startswith("sqlite://"):
        return url.removeprefix("sqlite://")
    return url


def _connect_sqlite(config: dict[str, Any]) -> sqlite3.Connection:
    url = os.environ.get(config["database"].get("url_env", "DATABASE_URL"))
    if not url:
        raise ValueError("DATABASE_URL is not set")
    path = _sqlite_path_from_url(url)
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _load_runtime() -> tuple[dict[str, Any], set[str], set[str]]:
    return load_config(), load_allowed_tables(), load_pii_columns()


def list_tables() -> list[str]:
    config, allowed_tables, _ = _load_runtime()
    if config["database"]["dialect"] != "sqlite":
        return sorted(allowed_tables)
    with _connect_sqlite(config) as conn:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
        ).fetchall()
    physical = {f"main.{row['name']}" for row in rows}
    return sorted(physical & allowed_tables)


def get_table_schema(table_name: str) -> dict[str, Any]:
    config, allowed_tables, _ = _load_runtime()
    if table_name not in allowed_tables:
        raise ValueError(f"Table is not allowed: {table_name}")
    schema, name = table_name.split(".", 1)
    if schema != "main":
        raise ValueError("SQLite Phase 1 schema inspection supports main schema only")
    with _connect_sqlite(config) as conn:
        rows = conn.execute(f"PRAGMA table_info({json.dumps(name)})").fetchall()
    return {
        "table": table_name,
        "columns": [
            {
                "name": row["name"],
                "type": row["type"],
                "notnull": bool(row["notnull"]),
                "primary_key": bool(row["pk"]),
            }
            for row in rows
        ],
    }


def run_readonly_sql(query: str) -> SqlToolResult:
    config, allowed_tables, pii_columns = _load_runtime()
    database = config["database"]
    dialect = database["dialect"]
    validate_readonly_sql(query, dialect, allowed_tables)
    if dialect != "sqlite":
        raise ValueError("Phase 1 execution wrapper currently supports sqlite")

    max_rows = int(database.get("max_rows", 100))
    max_bytes = int(database.get("max_result_bytes", config["runtime"]["max_tool_result_bytes"]))
    with _connect_sqlite(config) as conn:
        conn.execute(f"PRAGMA busy_timeout = {int(database.get('statement_timeout_seconds', 30)) * 1000}")
        cursor = conn.execute(query)
        raw_rows: list[dict[str, Any]] = []
        truncated = False
        for index, row in enumerate(cursor):
            if index >= max_rows:
                truncated = True
                break
            raw_rows.append(dict(row))
            if len(json.dumps(raw_rows, default=str).encode("utf-8")) > max_bytes:
                raw_rows.pop()
                truncated = True
                break

    redacted = redact_sql_rows(raw_rows, pii_columns, truncated=truncated)
    return {
        **redacted,
        "metadata": {
            "dialect": dialect,
            "tables": sorted(extract_tables(query, dialect)),
            "max_rows": max_rows,
            "max_result_bytes": max_bytes,
            "returned_rows": len(redacted["rows"]),
        },
    }
