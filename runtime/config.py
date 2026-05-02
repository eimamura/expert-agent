from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml


SUPPORTED_PROVIDERS = {"anthropic"}
SUPPORTED_DIALECTS = {"sqlite", "postgres", "mysql", "tsql", "databricks"}


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected YAML mapping in {path}")
    return data


def resolve_model_id(llm_config: dict[str, Any]) -> tuple[str, str | None]:
    raw_model = str(llm_config.get("model_id", "")).strip()
    aliases = llm_config.get("model_aliases") or {}
    if raw_model in aliases:
        return str(aliases[raw_model]), raw_model
    return raw_model, None


def validate_config(config: dict[str, Any]) -> dict[str, Any]:
    required = ["runtime", "llm", "database", "knowledge", "trace", "pricing"]
    missing = [key for key in required if key not in config]
    if missing:
        raise ValueError(f"Missing config sections: {', '.join(missing)}")

    runtime = config["runtime"]
    for key in [
        "max_steps",
        "max_total_tokens",
        "max_output_tokens_per_call",
        "max_run_cost_usd",
        "max_tool_result_bytes",
    ]:
        if runtime.get(key, 0) <= 0:
            raise ValueError(f"runtime.{key} must be positive")

    provider = config["llm"].get("provider")
    if provider not in SUPPORTED_PROVIDERS:
        raise ValueError(f"Unsupported LLM provider: {provider}")

    model_id, alias = resolve_model_id(config["llm"])
    if not model_id:
        raise ValueError("llm.model_id must be set")
    pricing = config["pricing"]
    if model_id not in pricing and (alias is None or alias not in pricing):
        raise ValueError(f"No pricing configured for model '{model_id}'")

    dialect = config["database"].get("dialect")
    if dialect not in SUPPORTED_DIALECTS:
        raise ValueError(f"Unsupported SQL dialect: {dialect}")

    return config


def load_config(path: Path | str = Path("config/app.yml")) -> dict[str, Any]:
    config = load_yaml(Path(path))
    return validate_config(config)


def runtime_snapshot(config: dict[str, Any]) -> dict[str, Any]:
    snapshot = deepcopy(config)
    model_id, alias = resolve_model_id(snapshot["llm"])
    snapshot["llm"]["model_id"] = model_id
    snapshot["llm"].pop("model_aliases", None)
    if alias:
        snapshot["llm"]["model_alias"] = alias
    return snapshot


def load_allowed_tables(path: Path | str = Path("rules/allowed_tables.yml")) -> set[str]:
    data = load_yaml(Path(path))
    return set(data.get("allowed_tables") or [])


def load_pii_columns(path: Path | str = Path("rules/pii_columns.yml")) -> set[str]:
    data = load_yaml(Path(path))
    return set(data.get("pii_columns") or [])
