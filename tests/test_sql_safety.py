from __future__ import annotations

import pytest

from tools.sql import extract_tables, validate_readonly_sql


ALLOWED = {"main.customers", "main.orders", "main.order_items", "main.products"}


@pytest.mark.parametrize(
    "query,tables",
    [
        ("SELECT COUNT(*) FROM main.orders", {"main.orders"}),
        (
            "WITH recent_orders AS (SELECT * FROM main.orders) SELECT COUNT(*) FROM recent_orders",
            {"main.orders"},
        ),
        ("SELECT * FROM (SELECT * FROM main.customers) c", {"main.customers"}),
    ],
)
def test_extract_tables_and_validate_allowed_selects(query: str, tables: set[str]) -> None:
    assert extract_tables(query, "sqlite") == tables
    validate_readonly_sql(query, "sqlite", ALLOWED)


@pytest.mark.parametrize(
    "query",
    [
        "DELETE FROM main.orders",
        "UPDATE main.customers SET email = 'x'",
        "INSERT INTO main.orders VALUES (1)",
        "DROP TABLE main.orders",
        "CREATE TABLE main.x AS SELECT * FROM main.orders",
        "SELECT * FROM main.orders; DROP TABLE main.orders;",
        "SELECT * FROM main.payments",
        "SELECT * FROM orders",
    ],
)
def test_validate_readonly_sql_rejects_unsafe_or_unapproved_sql(query: str) -> None:
    with pytest.raises(ValueError):
        validate_readonly_sql(query, "sqlite", ALLOWED)
