from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentState:
    run_id: str
    parent_run_id: str | None
    input_hash: str
    config_snapshot: dict[str, Any]
    messages: list[dict[str, Any]] = field(default_factory=list)
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    steps: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost_usd: float = 0.0
    final_status: str = "success"
    final_answer: str = ""
    error: dict[str, Any] | None = None
    limit_metadata: dict[str, Any] = field(default_factory=dict)
