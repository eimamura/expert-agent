from __future__ import annotations

import re

import pytest

from agents.prompts import SYSTEM_PROMPT_TEMPLATE
from runtime.config import load_config, runtime_snapshot, validate_config
from runtime.cost import CostTracker, estimate_call_cost_usd
from runtime.hashing import compute_input_hash, stable_json_dumps
from runtime.ids import new_run_id


def test_config_resolves_model_alias_to_concrete_model_id() -> None:
    config = load_config()
    snapshot = runtime_snapshot(config)
    assert snapshot["llm"]["model_id"] == "claude-sonnet-4-5"
    assert snapshot["llm"]["model_alias"] == "sonnet_latest"


def test_config_validates_hard_limits() -> None:
    config = load_config()
    config["runtime"]["max_steps"] = 0
    with pytest.raises(ValueError):
        validate_config(config)


def test_prompt_has_exactly_one_knowledge_placeholder() -> None:
    assert SYSTEM_PROMPT_TEMPLATE.count("{KNOWLEDGE_INDEX}") == 1
    assert "## Summary" in SYSTEM_PROMPT_TEMPLATE


def test_ulid_run_id_shape_and_sortable_length() -> None:
    run_id = new_run_id()
    assert len(run_id) == 26
    assert re.fullmatch(r"[0-9A-HJKMNP-TV-Z]{26}", run_id)


def test_stable_hashing_independent_of_key_order() -> None:
    left = {"b": 2, "a": [3, {"c": 4}]}
    right = {"a": [3, {"c": 4}], "b": 2}
    assert stable_json_dumps(left) == stable_json_dumps(right)
    assert compute_input_hash(left) == compute_input_hash(right)


def test_cost_estimation_and_limits() -> None:
    pricing = {"model": {"input_per_million_usd": 3.0, "output_per_million_usd": 15.0}}
    assert estimate_call_cost_usd("model", 1_000_000, 1_000_000, pricing) == 18.0
    tracker = CostTracker(max_total_tokens=10, max_run_cost_usd=1.0)
    tracker.add_call(8, 3, 0.5)
    assert tracker.exceeded_status() == "max_tokens_exceeded"
