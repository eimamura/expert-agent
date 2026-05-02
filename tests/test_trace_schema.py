from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.trace_reader import load_validated_trace
from runtime.trace_schema import TraceSchemaError, validate_trace_event


FIXTURE_ROOT = Path("fixtures/traces")


@pytest.mark.parametrize("path", sorted(FIXTURE_ROOT.glob("*.jsonl")))
def test_valid_trace_fixtures_pass_schema_validation(path: Path) -> None:
    events = load_validated_trace(path)
    assert events
    assert events[-1].event_type == "run_finished"


def test_trace_schema_negative_cases() -> None:
    base = {
        "schema_version": "1.0",
        "run_id": "run",
        "parent_run_id": None,
        "event_type": "llm_call",
        "timestamp": "2026-01-01T00:00:00.000Z",
        "provider": "anthropic",
        "model_id": "model",
        "input_tokens": 1,
        "output_tokens": 1,
        "cost_usd": 0.1,
        "input_summary_redacted": "in",
        "output_summary_redacted": "out",
    }
    for key in ["schema_version", "run_id", "event_type", "timestamp"]:
        event = dict(base)
        event.pop(key)
        with pytest.raises(TraceSchemaError):
            validate_trace_event(event)

    with pytest.raises(TraceSchemaError):
        validate_trace_event({**base, "schema_version": "2.0"})
    with pytest.raises(TraceSchemaError):
        validate_trace_event({**base, "event_type": "unknown"})
    with pytest.raises(TraceSchemaError):
        validate_trace_event({**base, "timestamp": "2026-01-01T00:00:00"})
    event = dict(base)
    event.pop("input_tokens")
    with pytest.raises(TraceSchemaError):
        validate_trace_event(event)
    with pytest.raises(TraceSchemaError):
        validate_trace_event(
            {
                "schema_version": "1.0",
                "run_id": "run",
                "parent_run_id": None,
                "event_type": "run_finished",
                "timestamp": "2026-01-01T00:00:00.000Z",
                "status": "bad",
                "steps": 1,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_cost_usd": 0.0,
                "error": None,
            }
        )


def test_unredacted_fixture_marker_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "bad.jsonl"
    event = json.loads((FIXTURE_ROOT / "success_basic.jsonl").read_text(encoding="utf-8").splitlines()[0])
    event["question"] = "email jane@example.com"
    path.write_text(json.dumps(event) + "\n", encoding="utf-8")
    with pytest.raises(TraceSchemaError, match="unredacted"):
        load_validated_trace(path)
