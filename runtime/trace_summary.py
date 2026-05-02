from __future__ import annotations

from pathlib import Path
from typing import Any

from runtime.trace_reader import load_validated_trace


def summarize_trace(path: Path | str) -> dict[str, Any]:
    trace_path = Path(path)
    events = load_validated_trace(trace_path)
    run_id = events[0].run_id
    tool_events = [event for event in events if event.event_type == "tool_call"]
    llm_events = [event for event in events if event.event_type == "llm_call"]
    finished = next(event for event in events if event.event_type == "run_finished")
    error = getattr(finished, "error", None)
    return {
        "run_id": run_id,
        "status": getattr(finished, "status"),
        "event_count": len(events),
        "tool_call_count": len(tool_events),
        "tools_used": [getattr(event, "tool_name") for event in tool_events],
        "total_input_tokens": getattr(finished, "total_input_tokens"),
        "total_output_tokens": getattr(finished, "total_output_tokens"),
        "estimated_total_cost_usd": getattr(finished, "total_cost_usd"),
        "llm_call_count": len(llm_events),
        "error_type": getattr(error, "type", None) if error else None,
        "error_source": getattr(error, "source", None) if error else None,
        "error_message": getattr(error, "message", None) if error else None,
        "trace_path": trace_path.as_posix(),
    }
