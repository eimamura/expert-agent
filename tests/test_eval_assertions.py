from __future__ import annotations

import pytest

from runtime.eval_assertions import assert_trace_case, has_partial_order
from runtime.trace_reader import load_validated_trace
from runtime.trace_schema import TraceSchemaError


def test_partial_order_allows_intervening_and_duplicate_tool_calls() -> None:
    assert has_partial_order(["a", "x", "b", "a"], ["a", "b"])
    assert has_partial_order(["a", "x", "b", "a"], ["b", "a"])
    assert not has_partial_order(["b", "a"], ["a", "b"])


def test_trace_case_assertions_positive_and_negative() -> None:
    events = load_validated_trace("fixtures/traces/success_basic.jsonl")
    assert_trace_case(
        events,
        {
            "expected_tools": ["read_knowledge_file"],
            "forbidden_tools": ["run_write_sql"],
            "tools_call_order": ["read_knowledge_file"],
            "expected_terminal_status": "success",
            "forbidden_output_markers": ["jane@example.com"],
        },
    )
    with pytest.raises(TraceSchemaError, match="required tool"):
        assert_trace_case(events, {"expected_tools": ["run_readonly_sql"]})
    with pytest.raises(TraceSchemaError, match="forbidden tool"):
        assert_trace_case(events, {"forbidden_tools": ["read_knowledge_file"]})
    with pytest.raises(TraceSchemaError, match="terminal status"):
        assert_trace_case(events, {"expected_terminal_status": "tool_error"})
