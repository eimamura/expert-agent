from __future__ import annotations

from pathlib import Path

import pytest

from runtime.trace_schema import TraceSchemaError
from runtime.trace_summary import summarize_trace


def test_trace_summary_contains_status_tools_tokens_cost_and_error() -> None:
    summary = summarize_trace("fixtures/traces/tool_error.jsonl")
    assert summary["status"] == "tool_error"
    assert summary["tool_call_count"] == 1
    assert summary["tools_used"] == ["read_knowledge_file"]
    assert summary["total_input_tokens"] == 10
    assert summary["estimated_total_cost_usd"] == 0.0001
    assert summary["error_type"] == "tool_error"
    assert summary["error_source"] == "tool"


def test_trace_summary_rejects_malformed_jsonl(tmp_path: Path) -> None:
    path = tmp_path / "bad.jsonl"
    path.write_text("{not json}\n", encoding="utf-8")
    with pytest.raises(TraceSchemaError, match="malformed JSONL"):
        summarize_trace(path)
