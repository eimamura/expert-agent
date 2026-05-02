from __future__ import annotations

import re
import pytest

from agents.prompts import SYSTEM_PROMPT_TEMPLATE
from runtime.config import (
    domain_path,
    knowledge_path,
    load_allowed_tables,
    load_config,
    runtime_snapshot,
    validate_config,
)
from runtime.cost import CostTracker, estimate_call_cost_usd
from runtime.hashing import compute_input_hash, sha256_text, stable_json_dumps
from runtime.ids import new_run_id
from runtime.knowledge_loader import build_knowledge_index
from runtime.loop import build_input_hash_parts


def test_config_resolves_model_alias_to_concrete_model_id() -> None:
    config = load_config()
    snapshot = runtime_snapshot(config)
    assert snapshot["llm"]["model_id"] == "claude-sonnet-4-5"
    assert snapshot["llm"]["model_alias"] == "sonnet_latest"


def test_config_uses_domain_pack_roots() -> None:
    config = load_config()
    assert config["domain"]["root"] == "domains/subscription_commerce"
    assert "root" not in config["knowledge"]
    assert knowledge_path(config).as_posix() == "domains/subscription_commerce/knowledge"
    assert domain_path(config, "rules", "allowed_tables.yml").as_posix() == (
        "domains/subscription_commerce/rules/allowed_tables.yml"
    )
    assert "main.customers" in load_allowed_tables(config)


def test_derived_knowledge_path_reads_domain_pack_markdown() -> None:
    config = load_config()
    index, source = build_knowledge_index(knowledge_path(config))
    paths = {item["path"] for item in source}
    assert "domain_overview.md" in paths
    assert "kpi_definitions.md" in paths
    assert "domain_overview.md" in index


def test_input_hash_parts_use_domain_rule_and_knowledge_hashes() -> None:
    config = load_config()
    snapshot = runtime_snapshot(config)
    _, knowledge_files = build_knowledge_index(knowledge_path(config))
    allowed_tables = load_allowed_tables(config)
    parts = build_input_hash_parts(
        question="What changed in monthly revenue?",
        config_snapshot=snapshot,
        knowledge_files=knowledge_files,
        allowed_tables=allowed_tables,
    )
    expected_redaction_hash = sha256_text(domain_path(config, "rules", "redaction.yml").read_text(encoding="utf-8"))
    assert parts["redaction_config_hash"] == expected_redaction_hash
    assert "root" not in parts["config_snapshot"]["knowledge"]
    assert all("sha256" in item for item in parts["knowledge_files"])
    assert compute_input_hash({**parts, "allowed_table_hash": "changed"}) != compute_input_hash(parts)


def test_config_validates_hard_limits() -> None:
    config = load_config()
    config["runtime"]["max_steps"] = 0
    with pytest.raises(ValueError):
        validate_config(config)


def test_config_requires_safe_relative_domain_root() -> None:
    config = load_config()
    config["domain"].pop("root")
    with pytest.raises(ValueError, match="domain.root"):
        validate_config(config)

    config = load_config()
    config["domain"]["root"] = "/tmp/domain"
    with pytest.raises(ValueError, match="relative repository path"):
        validate_config(config)

    config = load_config()
    config["domain"]["root"] = "domains/../secrets"
    with pytest.raises(ValueError, match="relative repository path"):
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
