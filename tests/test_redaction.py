from __future__ import annotations

import json
from pathlib import Path

from runtime.redaction import REDACTION_TOKEN, redact_jsonable, redact_sql_rows, redact_text
from runtime.trace import TraceWriter


def test_redact_text_applies_configured_patterns() -> None:
    text = "email jane@example.com token=abcdefgh123456 phone 555-123-4567 db postgres://u:p@localhost/db"
    redacted = redact_text(text)
    assert "jane@example.com" not in redacted
    assert "abcdefgh123456" not in redacted
    assert "555-123-4567" not in redacted
    assert "postgres://u:p@localhost/db" not in redacted
    assert REDACTION_TOKEN in redacted


def test_redact_sql_rows_exact_keys_nested_and_types() -> None:
    rows = [
        {
            "customer_id": 1,
            "email": "jane@example.com",
            "profile": {"phone": "555-123-4567", "score": 9.5},
            "items": [{"ssn": "123-45-6789", "qty": 2}],
        }
    ]
    result = redact_sql_rows(rows, {"email", "phone", "ssn"})
    assert result["rows"][0]["customer_id"] == 1
    assert result["rows"][0]["profile"]["score"] == 9.5
    assert result["rows"][0]["email"] == REDACTION_TOKEN
    assert result["rows"][0]["profile"]["phone"] == REDACTION_TOKEN
    assert result["rows"][0]["items"][0]["ssn"] == REDACTION_TOKEN
    assert result["redacted_columns"] == ["email", "phone", "ssn"]
    assert result["row_count"] == 1
    assert result["truncated"] is False


def test_redact_jsonable_protects_llm_visible_tool_output() -> None:
    value = {"content": "customer jane@example.com token=abcdefgh123456"}
    redacted = redact_jsonable(value)
    serialized = json.dumps(redacted)
    assert "jane@example.com" not in serialized
    assert "abcdefgh123456" not in serialized
    assert REDACTION_TOKEN in serialized


def test_trace_persistence_redacts_error_metadata(tmp_path: Path) -> None:
    trace = TraceWriter(tmp_path, "run-redaction")
    trace.run_started(input_hash="hash", config_snapshot={}, question="token=abcdefgh123456")
    trace.run_finished(
        status="llm_error",
        steps=1,
        total_input_tokens=0,
        total_output_tokens=0,
        total_cost_usd=0,
        error={
            "type": "provider_error",
            "message": "failed for jane@example.com token=abcdefgh123456",
            "retryable": False,
            "source": "provider",
        },
    )
    serialized = trace.path.read_text(encoding="utf-8")
    assert "jane@example.com" not in serialized
    assert "abcdefgh123456" not in serialized
    assert REDACTION_TOKEN in serialized
