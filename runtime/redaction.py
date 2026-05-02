from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, TypedDict
import re

import yaml


REDACTION_TOKEN = "[REDACTED]"
DEFAULT_RULES_PATH = Path("rules/redaction.yml")


class RedactedSqlResult(TypedDict):
    rows: list[dict[str, Any]]
    redacted_columns: list[str]
    row_count: int
    truncated: bool


def _load_patterns(path: Path = DEFAULT_RULES_PATH) -> list[re.Pattern[str]]:
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return [re.compile(item["regex"]) for item in data.get("patterns", [])]


def redact_text(text: str) -> str:
    if not isinstance(text, str):
        raise TypeError("redact_text() expects a string")
    redacted = text
    for pattern in _load_patterns():
        redacted = pattern.sub(REDACTION_TOKEN, redacted)
    return redacted


def _redact_value(value: Any, pii_columns: set[str], redacted_columns: set[str]) -> Any:
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, child in value.items():
            if key in pii_columns:
                redacted_columns.add(key)
                result[key] = REDACTION_TOKEN
            else:
                result[key] = _redact_value(child, pii_columns, redacted_columns)
        return result
    if isinstance(value, list):
        return [_redact_value(item, pii_columns, redacted_columns) for item in value]
    return deepcopy(value)


def redact_sql_rows(
    rows: list[dict[str, Any]],
    pii_columns: set[str],
    truncated: bool = False,
) -> RedactedSqlResult:
    redacted_columns: set[str] = set()
    redacted_rows = [_redact_value(row, pii_columns, redacted_columns) for row in rows]
    return {
        "rows": redacted_rows,
        "redacted_columns": sorted(redacted_columns),
        "row_count": len(rows),
        "truncated": truncated,
    }
