from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

import app.api as api_module
from runtime.run_store import RunStore


@pytest.fixture
def store(tmp_path):
    return RunStore(tmp_path / "runs.db")


@pytest.fixture
def trace_dir(tmp_path):
    d = tmp_path / "traces"
    d.mkdir()
    return d


@pytest.fixture
def test_config(trace_dir):
    return {"trace": {"dir": str(trace_dir)}}


@pytest.fixture
def client(store, test_config):
    with (
        patch.object(api_module, "_run_store", store),
        patch.object(api_module, "_config", test_config),
        patch.object(api_module, "_run_in_background"),
    ):
        yield TestClient(api_module.app)


def test_create_run_returns_202(client):
    resp = client.post("/runs", json={"question": "What is MRR?"})
    assert resp.status_code == 202
    data = resp.json()
    assert "run_id" in data
    assert data["status"] == "queued"


def test_create_run_persists_to_store(client, store):
    resp = client.post("/runs", json={"question": "What is MRR?"})
    run_id = resp.json()["run_id"]
    run = store.get_run(run_id)
    assert run is not None
    assert run["status"] == "queued"


def test_create_run_redacts_question(client, store):
    resp = client.post("/runs", json={"question": "Email: jane@example.com"})
    run_id = resp.json()["run_id"]
    run = store.get_run(run_id)
    assert "jane@example.com" not in (run["question"] or "")


def test_get_run_returns_200(client, store):
    resp = client.post("/runs", json={"question": "test"})
    run_id = resp.json()["run_id"]
    resp2 = client.get(f"/runs/{run_id}")
    assert resp2.status_code == 200
    data = resp2.json()
    assert data["run_id"] == run_id
    assert data["status"] == "queued"


def test_get_run_excludes_config_snapshot(client, store):
    resp = client.post("/runs", json={"question": "test"})
    run_id = resp.json()["run_id"]
    resp2 = client.get(f"/runs/{run_id}")
    assert "config_snapshot" not in resp2.json()


def test_get_run_not_found(client):
    resp = client.get("/runs/NOTEXIST")
    assert resp.status_code == 404


def test_get_trace_not_found_when_run_missing(client):
    resp = client.get("/runs/NOTEXIST/trace")
    assert resp.status_code == 404


def test_get_trace_not_found_when_no_trace_file(client, store):
    resp = client.post("/runs", json={"question": "test"})
    run_id = resp.json()["run_id"]
    resp2 = client.get(f"/runs/{run_id}/trace")
    assert resp2.status_code == 404


def test_get_trace_returns_events(client, store, trace_dir, tmp_path):
    fixture_src = Path("fixtures/traces/success_basic.jsonl")
    if not fixture_src.exists():
        pytest.skip("success_basic.jsonl fixture not found")
    resp = client.post("/runs", json={"question": "test"})
    run_id = resp.json()["run_id"]
    dest = trace_dir / f"{run_id}.jsonl"
    dest.write_bytes(fixture_src.read_bytes())
    resp2 = client.get(f"/runs/{run_id}/trace")
    assert resp2.status_code == 200
    data = resp2.json()
    assert data["run_id"] == run_id
    assert isinstance(data["events"], list)
    assert len(data["events"]) > 0


def test_create_run_503_when_not_initialized():
    with (
        patch.object(api_module, "_run_store", None),
        patch.object(api_module, "_config", {}),
    ):
        c = TestClient(api_module.app, raise_server_exceptions=False)
        resp = c.post("/runs", json={"question": "test"})
        assert resp.status_code == 503


def test_get_run_503_when_not_initialized():
    with patch.object(api_module, "_run_store", None):
        c = TestClient(api_module.app, raise_server_exceptions=False)
        resp = c.get("/runs/anything")
        assert resp.status_code == 503
