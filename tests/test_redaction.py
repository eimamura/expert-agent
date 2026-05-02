from __future__ import annotations

from runtime.redaction import REDACTION_TOKEN, redact_sql_rows, redact_text


def test_redact_text_applies_configured_patterns() -> None:
    text = "email jane@example.com token=abcdefgh123456 phone 555-123-4567"
    redacted = redact_text(text)
    assert "jane@example.com" not in redacted
    assert "abcdefgh123456" not in redacted
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
