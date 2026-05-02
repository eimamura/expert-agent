from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from runtime.redaction import REDACTION_TOKEN
from runtime.trace_schema import TraceEvent, TraceSchemaError, validate_trace_events


SENSITIVE_FIXTURE_MARKERS = [
    "jane@example.com",
    "a@b.com",
    "555-123-4567",
    "token=abcdefgh",
    "sk-live",
]


def read_trace_jsonl(path: Path | str) -> list[dict[str, Any]]:
    trace_path = Path(path)
    events: list[dict[str, Any]] = []
    for line_number, line in enumerate(trace_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise TraceSchemaError(f"malformed JSONL at line {line_number}: {exc.msg}") from exc
        if not isinstance(event, dict):
            raise TraceSchemaError(f"trace line {line_number} is not a JSON object")
        events.append(event)
    if not events:
        raise TraceSchemaError("trace is empty")
    return events


def load_validated_trace(path: Path | str) -> list[TraceEvent]:
    events = read_trace_jsonl(path)
    serialized = json.dumps(events, sort_keys=True, default=str)
    for marker in SENSITIVE_FIXTURE_MARKERS:
        if marker in serialized:
            raise TraceSchemaError("trace contains an unredacted sensitive fixture marker")
    return validate_trace_events(events)


def assert_trace_replayable(path: Path | str, *, expected_status: str | None = None) -> list[TraceEvent]:
    events = load_validated_trace(path)
    finished = [event for event in events if event.event_type == "run_finished"]
    if len(finished) != 1:
        raise TraceSchemaError("trace must contain exactly one run_finished event")
    if expected_status and getattr(finished[0], "status") != expected_status:
        raise TraceSchemaError(f"expected status {expected_status}, got {getattr(finished[0], 'status')}")
    return events
