from __future__ import annotations

import os
import sqlite3
from pathlib import Path

import pytest

import tools.sql as sql_tools


@pytest.fixture()
def sqlite_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    db_path = tmp_path / "local.sqlite"
    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE customers (customer_id INTEGER PRIMARY KEY, email TEXT, name TEXT);
        CREATE TABLE orders (order_id INTEGER PRIMARY KEY, customer_id INTEGER, order_total REAL, status TEXT);
        INSERT INTO customers VALUES (1, 'jane@example.com', 'Jane');
        INSERT INTO orders VALUES (10, 1, 42.5, 'paid');
        """
    )
    conn.commit()
    conn.close()
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    return db_path


def test_list_tables_and_schema(sqlite_db: Path) -> None:
    assert "main.customers" in sql_tools.list_tables()
    schema = sql_tools.get_table_schema("main.customers")
    assert [column["name"] for column in schema["columns"]] == ["customer_id", "email", "name"]


def test_run_readonly_sql_redacts_and_returns_metadata(sqlite_db: Path) -> None:
    result = sql_tools.run_readonly_sql("SELECT customer_id, email FROM main.customers")
    assert result["rows"] == [{"customer_id": 1, "email": "[REDACTED]"}]
    assert result["redacted_columns"] == ["email"]
    assert result["metadata"]["tables"] == ["main.customers"]


def test_run_readonly_sql_validates_before_execution(sqlite_db: Path) -> None:
    with pytest.raises(ValueError):
        sql_tools.run_readonly_sql("UPDATE main.customers SET email = 'x'")
