from __future__ import annotations

import pytest

from runtime.provider_double import (
    ProviderDouble,
    ScriptedProviderError,
    ScriptedProviderTimeout,
    final_answer,
    tool_request,
)


def test_provider_double_returns_scripted_final_answer() -> None:
    provider = ProviderDouble([final_answer("done", input_tokens=3, output_tokens=4)])
    response = provider.call(
        system_prompt="system",
        messages=[{"role": "user", "content": "q"}],
        tools=[],
        model_id="model",
        max_output_tokens=100,
        temperature=0,
    )
    assert response["content"][0]["text"] == "done"
    assert response["usage"] == {"input_tokens": 3, "output_tokens": 4}
    assert provider.calls[0]["messages"][0]["content"] == "q"


def test_provider_double_returns_tool_request() -> None:
    response = ProviderDouble([tool_request("list_tables", {})]).call(
        system_prompt="system",
        messages=[],
        tools=[],
        model_id="model",
        max_output_tokens=100,
        temperature=0,
    )
    assert response["content"][0]["type"] == "tool_use"
    assert response["content"][0]["name"] == "list_tables"


def test_provider_double_errors_timeouts_and_malformed_responses() -> None:
    with pytest.raises(ScriptedProviderError):
        ProviderDouble([{"action": "error", "message": "failed"}]).call(
            system_prompt="", messages=[], tools=[], model_id="", max_output_tokens=1, temperature=0
        )
    with pytest.raises(ScriptedProviderTimeout):
        ProviderDouble([{"action": "timeout", "message": "slow"}]).call(
            system_prompt="", messages=[], tools=[], model_id="", max_output_tokens=1, temperature=0
        )
    response = ProviderDouble([{"action": "malformed", "content": "bad"}]).call(
        system_prompt="", messages=[], tools=[], model_id="", max_output_tokens=1, temperature=0
    )
    assert response["content"] == "bad"
