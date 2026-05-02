from __future__ import annotations

from pathlib import Path

import pytest

from runtime.trace_reader import assert_trace_replayable
from runtime.trace_schema import TraceSchemaError


def test_trace_replay_validates_structure_and_expected_status() -> None:
    events = assert_trace_replayable("fixtures/traces/success_basic.jsonl", expected_status="success")
    assert [event.event_type for event in events][0] == "run_started"


def test_trace_replay_rejects_wrong_status_and_missing_terminal_event(tmp_path: Path) -> None:
    with pytest.raises(TraceSchemaError, match="expected status"):
        assert_trace_replayable("fixtures/traces/success_basic.jsonl", expected_status="tool_error")

    path = tmp_path / "missing_finished.jsonl"
    first_line = Path("fixtures/traces/success_basic.jsonl").read_text(encoding="utf-8").splitlines()[0]
    path.write_text(first_line + "\n", encoding="utf-8")
    with pytest.raises(TraceSchemaError, match="missing run_finished"):
        assert_trace_replayable(path)
