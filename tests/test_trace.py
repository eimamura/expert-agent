from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest

from runtime.trace import TraceWriter


def _load_events(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_trace_required_fields_redaction_and_status(tmp_path: Path) -> None:
    trace = TraceWriter(tmp_path, "01H00000000000000000000000")
    trace.run_started(input_hash="abc", config_snapshot={"llm": {"model_id": "m"}}, question="email a@b.com")
    trace.llm_call(
        provider="anthropic",
        model_id="m",
        input_tokens=1,
        output_tokens=2,
        cost_usd=0.01,
        input_summary="token=abcdefgh",
        output_summary="hello jane@example.com",
    )
    trace.tool_call(
        tool_name="run_readonly_sql",
        arguments={"query": "SELECT email FROM main.customers"},
        status="success",
        output_sample={"rows": [{"email": "[REDACTED]"}]},
        output_sample_strategy="head",
        output_sample_size=5,
        redacted_columns=["email"],
        error=None,
    )
    trace.run_finished(
        status="success",
        steps=1,
        total_input_tokens=1,
        total_output_tokens=2,
        total_cost_usd=0.01,
        error=None,
    )
    events = _load_events(trace.path)
    assert {event["event_type"] for event in events} == {"run_started", "llm_call", "tool_call", "run_finished"}
    for event in events:
        assert event["schema_version"] == "1.0"
        assert event["parent_run_id"] is None
        assert event["timestamp"].endswith("Z")
        datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00"))
    serialized = trace.path.read_text(encoding="utf-8")
    assert "a@b.com" not in serialized
    assert "jane@example.com" not in serialized
    assert "[REDACTED]" in serialized


def test_trace_rejects_invalid_run_finished_status(tmp_path: Path) -> None:
    trace = TraceWriter(tmp_path, "01H00000000000000000000000")
    with pytest.raises(ValueError):
        trace.run_finished(
            status="bad",
            steps=1,
            total_input_tokens=0,
            total_output_tokens=0,
            total_cost_usd=0,
            error=None,
        )
