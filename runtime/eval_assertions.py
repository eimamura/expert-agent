from __future__ import annotations

from typing import Any

from runtime.trace_schema import TraceEvent, TraceSchemaError


def tool_names(events: list[TraceEvent]) -> list[str]:
    return [getattr(event, "tool_name") for event in events if event.event_type == "tool_call"]


def has_partial_order(actual: list[str], expected: list[str]) -> bool:
    cursor = 0
    for tool in expected:
        try:
            index = actual.index(tool, cursor)
        except ValueError:
            return False
        cursor = index + 1
    return True


def assert_trace_case(events: list[TraceEvent], case: dict[str, Any]) -> None:
    actual_tools = tool_names(events)
    for tool in case.get("expected_tools", []):
        if tool not in actual_tools:
            raise TraceSchemaError(f"required tool was not used: {tool}")
    for tool in case.get("forbidden_tools", []):
        if tool in actual_tools:
            raise TraceSchemaError(f"forbidden tool was used: {tool}")
    expected_order = case.get("tools_call_order", [])
    if expected_order and not has_partial_order(actual_tools, expected_order):
        raise TraceSchemaError(f"tool calls do not satisfy partial order: {expected_order}")
    expected_status = case.get("expected_terminal_status")
    if expected_status:
        statuses = [getattr(event, "status") for event in events if event.event_type == "run_finished"]
        if statuses != [expected_status]:
            raise TraceSchemaError(f"expected terminal status {expected_status}, got {statuses}")
    for event in events:
        if event.event_type == "llm_call":
            for field in ("input_tokens", "output_tokens", "cost_usd"):
                if getattr(event, field) is None:
                    raise TraceSchemaError(f"llm_call missing {field}")
        if event.event_type == "tool_call":
            serialized = str(getattr(event, "output_sample_redacted"))
            for marker in case.get("forbidden_output_markers", []):
                if marker in serialized:
                    raise TraceSchemaError(f"tool output contains forbidden marker: {marker}")
