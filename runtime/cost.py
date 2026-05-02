from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


def estimate_call_cost_usd(
    model_id: str,
    input_tokens: int,
    output_tokens: int,
    pricing: Mapping[str, Mapping[str, float]],
    model_alias: str | None = None,
) -> float:
    price = pricing.get(model_id)
    if price is None and model_alias is not None:
        price = pricing.get(model_alias)
    if price is None:
        raise KeyError(f"No pricing configured for model '{model_id}'")
    input_cost = input_tokens * float(price["input_per_million_usd"]) / 1_000_000
    output_cost = output_tokens * float(price["output_per_million_usd"]) / 1_000_000
    return input_cost + output_cost


@dataclass
class CostTracker:
    max_total_tokens: int
    max_run_cost_usd: float
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost_usd: float = 0.0

    @property
    def total_tokens(self) -> int:
        return self.total_input_tokens + self.total_output_tokens

    def add_call(self, input_tokens: int, output_tokens: int, cost_usd: float) -> None:
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_cost_usd += cost_usd

    def exceeded_status(self) -> str | None:
        if self.total_tokens > self.max_total_tokens:
            return "max_tokens_exceeded"
        if self.total_cost_usd > self.max_run_cost_usd:
            return "max_cost_exceeded"
        return None
