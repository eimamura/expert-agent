from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    parent_run_id TEXT,
    question TEXT,
    status TEXT NOT NULL DEFAULT 'queued',
    created_at TEXT NOT NULL,
    finished_at TEXT,
    total_input_tokens INTEGER,
    total_output_tokens INTEGER,
    total_cost_usd REAL,
    final_answer TEXT,
    input_hash TEXT,
    config_snapshot TEXT,
    error_type TEXT,
    error_message TEXT
)
"""

_UPDATABLE_FIELDS = frozenset({
    "status",
    "finished_at",
    "total_input_tokens",
    "total_output_tokens",
    "total_cost_usd",
    "final_answer",
    "input_hash",
    "config_snapshot",
    "error_type",
    "error_message",
})


class RunStore:
    def __init__(self, db_path: Path | str = Path("runs.db")) -> None:
        self.db_path = Path(db_path)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(_CREATE_TABLE)

    def create_run(
        self,
        *,
        run_id: str,
        question: str,
        input_hash: str,
        config_snapshot: dict[str, Any],
        created_at: str,
        parent_run_id: str | None = None,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO runs
                    (run_id, parent_run_id, question, status, created_at, input_hash, config_snapshot)
                VALUES (?, ?, ?, 'queued', ?, ?, ?)
                """,
                (
                    run_id,
                    parent_run_id,
                    question,
                    created_at,
                    input_hash,
                    json.dumps(config_snapshot),
                ),
            )

    def update_run(self, run_id: str, **kwargs: Any) -> None:
        fields = {k: v for k, v in kwargs.items() if k in _UPDATABLE_FIELDS}
        if not fields:
            return
        if "config_snapshot" in fields and isinstance(fields["config_snapshot"], dict):
            fields["config_snapshot"] = json.dumps(fields["config_snapshot"])
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [run_id]
        with self._connect() as conn:
            conn.execute(f"UPDATE runs SET {set_clause} WHERE run_id = ?", values)

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM runs WHERE run_id = ?", (run_id,)
            ).fetchone()
        if row is None:
            return None
        result = dict(row)
        if result.get("config_snapshot"):
            try:
                result["config_snapshot"] = json.loads(result["config_snapshot"])
            except (json.JSONDecodeError, TypeError):
                pass
        return result
