from __future__ import annotations

import pytest
from runtime.run_store import RunStore


@pytest.fixture
def store(tmp_path):
    return RunStore(tmp_path / "runs.db")


def _make_run(store: RunStore, run_id: str = "01ABC", question: str = "What is MRR?") -> None:
    store.create_run(
        run_id=run_id,
        question=question,
        input_hash="hash123",
        config_snapshot={"llm": {"model_id": "test"}},
        created_at="2026-01-01T00:00:00Z",
    )


def test_create_and_get_run(store):
    _make_run(store)
    run = store.get_run("01ABC")
    assert run is not None
    assert run["run_id"] == "01ABC"
    assert run["status"] == "queued"
    assert run["question"] == "What is MRR?"
    assert run["input_hash"] == "hash123"
    assert run["config_snapshot"] == {"llm": {"model_id": "test"}}
    assert run["parent_run_id"] is None


def test_get_nonexistent_run_returns_none(store):
    assert store.get_run("NOTEXIST") is None


def test_update_status(store):
    _make_run(store)
    store.update_run("01ABC", status="running")
    assert store.get_run("01ABC")["status"] == "running"


def test_update_finished(store):
    _make_run(store)
    store.update_run(
        "01ABC",
        status="success",
        finished_at="2026-01-01T00:01:00Z",
        total_input_tokens=100,
        total_output_tokens=200,
        total_cost_usd=0.005,
        final_answer="The MRR is $10,000.",
        input_hash="newhash",
    )
    run = store.get_run("01ABC")
    assert run["status"] == "success"
    assert run["finished_at"] == "2026-01-01T00:01:00Z"
    assert run["total_input_tokens"] == 100
    assert run["total_output_tokens"] == 200
    assert run["total_cost_usd"] == pytest.approx(0.005)
    assert run["final_answer"] == "The MRR is $10,000."
    assert run["input_hash"] == "newhash"


def test_update_error(store):
    _make_run(store)
    store.update_run("01ABC", status="llm_error", error_type="provider_error", error_message="timeout")
    run = store.get_run("01ABC")
    assert run["status"] == "llm_error"
    assert run["error_type"] == "provider_error"
    assert run["error_message"] == "timeout"


def test_update_config_snapshot(store):
    _make_run(store)
    store.update_run("01ABC", config_snapshot={"llm": {"model_id": "updated"}})
    run = store.get_run("01ABC")
    assert run["config_snapshot"] == {"llm": {"model_id": "updated"}}


def test_update_ignores_unknown_fields(store):
    _make_run(store)
    store.update_run("01ABC", unknown_field="ignored", status="running")
    run = store.get_run("01ABC")
    assert run["status"] == "running"
    assert "unknown_field" not in run


def test_update_with_no_valid_fields_is_noop(store):
    _make_run(store)
    store.update_run("01ABC", unknown="ignored")
    assert store.get_run("01ABC")["status"] == "queued"


def test_create_run_with_parent(store):
    _make_run(store, run_id="parent01")
    store.create_run(
        run_id="child01",
        question="Follow-up",
        input_hash="h2",
        config_snapshot={},
        created_at="2026-01-01T00:00:01Z",
        parent_run_id="parent01",
    )
    run = store.get_run("child01")
    assert run["parent_run_id"] == "parent01"


def test_multiple_runs_independent(store):
    _make_run(store, run_id="run_a")
    _make_run(store, run_id="run_b", question="Other question")
    store.update_run("run_a", status="success")
    assert store.get_run("run_a")["status"] == "success"
    assert store.get_run("run_b")["status"] == "queued"
