from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from runtime.config import load_config
from runtime.provider_double import ProviderDouble, final_answer, tool_request
from runtime.loop import run_agent


def _config(tmp_path: Path) -> dict[str, Any]:
    config = load_config()
    config["trace"]["dir"] = str(tmp_path)
    config["runtime"]["max_steps"] = 3
    config["runtime"]["max_total_tokens"] = 1000
    config["runtime"]["max_run_cost_usd"] = 1.0
    return config


def _events(tmp_path: Path, run_id: str) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in (tmp_path / f"{run_id}.jsonl").read_text(encoding="utf-8").splitlines()
    ]


def test_runtime_successful_final_answer_with_provider_double(tmp_path: Path) -> None:
    provider = ProviderDouble([final_answer("## Summary\nDone.")])
    state = run_agent("Question?", _config(tmp_path), provider=provider, run_id="run-success")
    assert state.final_status == "success"
    assert "## Summary" in state.final_answer


def test_runtime_tool_flow_redacts_llm_visible_tool_output(tmp_path: Path) -> None:
    provider = ProviderDouble(
        [
            tool_request("read_knowledge_file", {"path": "domain_overview.md"}),
            final_answer("## Summary\nDone."),
        ]
    )
    state = run_agent("Question?", _config(tmp_path), provider=provider, run_id="run-tool")
    assert state.final_status == "success"
    second_call_messages = provider.calls[1]["messages"]
    assert any("Domain Overview" in json.dumps(message) for message in second_call_messages)


def test_runtime_provider_error_timeout_and_malformed_response(tmp_path: Path) -> None:
    provider_error = ProviderDouble([{"action": "error", "message": "failed token=abcdefgh123456"}])
    state = run_agent("Question?", _config(tmp_path), provider=provider_error, run_id="run-provider-error")
    assert state.final_status == "llm_error"
    assert state.error and state.error["type"] == "provider_error"
    assert "abcdefgh123456" not in (tmp_path / "run-provider-error.jsonl").read_text(encoding="utf-8")

    timeout = ProviderDouble([{"action": "timeout", "message": "slow token=abcdefgh123456"}])
    state = run_agent("Question?", _config(tmp_path), provider=timeout, run_id="run-timeout")
    assert state.final_status == "timeout_error"
    assert state.error and state.error["type"] == "timeout_error"
    assert "abcdefgh123456" not in (tmp_path / "run-timeout.jsonl").read_text(encoding="utf-8")

    malformed = ProviderDouble([{"action": "malformed", "content": "bad"}])
    state = run_agent("Question?", _config(tmp_path), provider=malformed, run_id="run-malformed")
    assert state.final_status == "validation_error"
    assert state.error and state.error["source"] == "validator"


def test_runtime_budget_and_tool_truncation_reporting(tmp_path: Path) -> None:
    config = _config(tmp_path)
    config["runtime"]["max_total_tokens"] = 10
    provider = ProviderDouble([final_answer("expensive", input_tokens=9, output_tokens=2)])
    state = run_agent("Question?", config, provider=provider, run_id="run-budget")
    assert state.final_status == "max_tokens_exceeded"
    finished = _events(tmp_path, "run-budget")[-1]
    assert finished["error"]["type"] == "budget_error"
    assert finished["limit_metadata"]["observed_total_tokens"] == 11

    config = _config(tmp_path)
    config["runtime"]["max_tool_result_bytes"] = 20
    provider = ProviderDouble(
        [
            tool_request("read_knowledge_file", {"path": "domain_overview.md"}),
            final_answer("## Summary\nDone."),
        ]
    )
    run_agent("Question?", config, provider=provider, run_id="run-truncate")
    tool_event = [event for event in _events(tmp_path, "run-truncate") if event["event_type"] == "tool_call"][0]
    assert tool_event["tool_result_truncated"] is True
    assert tool_event["max_tool_result_bytes"] == 20
    assert tool_event["observed_tool_result_bytes"] > 20
