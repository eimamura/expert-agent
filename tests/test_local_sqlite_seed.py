from __future__ import annotations

from pathlib import Path

import pytest

import tools.sql as sql_tools
from scripts.create_local_sqlite import create_local_sqlite


def test_create_local_sqlite_refuses_to_overwrite_existing_file(tmp_path: Path) -> None:
    db_path = tmp_path / "local.sqlite"
    create_local_sqlite(db_path)

    with pytest.raises(FileExistsError):
        create_local_sqlite(db_path)


def test_create_local_sqlite_supports_sql_tools(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db_path = create_local_sqlite(tmp_path / "local.sqlite")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")

    assert sql_tools.list_tables() == [
        "main.customers",
        "main.order_items",
        "main.orders",
        "main.products",
    ]

    result = sql_tools.run_readonly_sql(
        "SELECT customer_id, email, phone FROM main.customers ORDER BY customer_id LIMIT 1"
    )
    assert result["rows"] == [
        {
            "customer_id": 1,
            "email": "[REDACTED]",
            "phone": "[REDACTED]",
        }
    ]
    assert result["redacted_columns"] == ["email", "phone"]
