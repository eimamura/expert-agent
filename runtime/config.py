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
    required = ["runtime", "llm", "database", "domain", "knowledge", "trace", "pricing"]
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
        "provider_timeout_seconds",
        "tool_timeout_seconds",
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

    domain_root = str(config["domain"].get("root", "")).strip()
    if not domain_root:
        raise ValueError("domain.root must be set")
    domain_path = Path(domain_root)
    if domain_path.is_absolute() or ".." in domain_path.parts:
        raise ValueError("domain.root must be a relative repository path")

    if config["knowledge"].get("max_file_read_bytes", 0) <= 0:
        raise ValueError("knowledge.max_file_read_bytes must be positive")

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


def domain_path(config: dict[str, Any], *parts: str) -> Path:
    return Path(config["domain"]["root"], *parts)


def knowledge_path(config: dict[str, Any]) -> Path:
    return domain_path(config, "knowledge")


def load_allowed_tables(config_or_path: dict[str, Any] | Path | str | None = None) -> set[str]:
    if config_or_path is None:
        path = domain_path(load_config(), "rules", "allowed_tables.yml")
    elif isinstance(config_or_path, dict):
        path = domain_path(config_or_path, "rules", "allowed_tables.yml")
    else:
        path = Path(config_or_path)
    data = load_yaml(path)
    return set(data.get("allowed_tables") or [])


def load_pii_columns(config_or_path: dict[str, Any] | Path | str | None = None) -> set[str]:
    if config_or_path is None:
        path = domain_path(load_config(), "rules", "pii_columns.yml")
    elif isinstance(config_or_path, dict):
        path = domain_path(config_or_path, "rules", "pii_columns.yml")
    else:
        path = Path(config_or_path)
    data = load_yaml(path)
    return set(data.get("pii_columns") or [])
