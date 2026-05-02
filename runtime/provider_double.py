from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class ScriptedProviderError(RuntimeError):
    pass


class ScriptedProviderTimeout(TimeoutError):
    pass


@dataclass
class ProviderDouble:
    script: list[dict[str, Any]]
    calls: list[dict[str, Any]] = field(default_factory=list)
    index: int = 0

    def call(
        self,
        *,
        system_prompt: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        model_id: str,
        max_output_tokens: int,
        temperature: float,
    ) -> dict[str, Any]:
        self.calls.append(
            {
                "system_prompt": system_prompt,
                "messages": messages.copy(),
                "tools": tools,
                "model_id": model_id,
                "max_output_tokens": max_output_tokens,
                "temperature": temperature,
            }
        )
        if self.index >= len(self.script):
            raise ScriptedProviderError("ProviderDouble script exhausted")
        item = self.script[self.index]
        self.index += 1
        action = item.get("action", "response")
        if action == "error":
            raise ScriptedProviderError(str(item.get("message", "scripted provider error")))
        if action == "timeout":
            raise ScriptedProviderTimeout(str(item.get("message", "scripted provider timeout")))
        if action == "malformed":
            return {"content": item.get("content", "malformed"), "usage": item.get("usage", {})}
        return {
            "content": item.get("content", []),
            "stop_reason": item.get("stop_reason"),
            "usage": {
                "input_tokens": int(item.get("usage", {}).get("input_tokens", 0)),
                "output_tokens": int(item.get("usage", {}).get("output_tokens", 0)),
            },
        }


def final_answer(text: str, *, input_tokens: int = 10, output_tokens: int = 10) -> dict[str, Any]:
    return {
        "content": [{"type": "text", "text": text}],
        "usage": {"input_tokens": input_tokens, "output_tokens": output_tokens},
    }


def tool_request(
    name: str,
    arguments: dict[str, Any],
    *,
    tool_id: str = "toolu_1",
    text: str = "",
    input_tokens: int = 10,
    output_tokens: int = 10,
) -> dict[str, Any]:
    content: list[dict[str, Any]] = []
    if text:
        content.append({"type": "text", "text": text})
    content.append({"type": "tool_use", "id": tool_id, "name": name, "input": arguments})
    return {
        "content": content,
        "usage": {"input_tokens": input_tokens, "output_tokens": output_tokens},
    }
