from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from runtime.redaction import redact_text


SCHEMA_VERSION = "1.0"
RUN_FINISHED_STATUSES = {
    "success",
    "max_steps_exceeded",
    "max_tokens_exceeded",
    "max_cost_exceeded",
    "tool_error",
    "llm_error",
    "validation_error",
}


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _redact_jsonable(value: Any) -> Any:
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, list):
        return [_redact_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: _redact_jsonable(child) for key, child in value.items()}
    return value


class TraceWriter:
    def __init__(self, trace_dir: Path, run_id: str, parent_run_id: str | None = None) -> None:
        self.trace_dir = trace_dir
        self.run_id = run_id
        self.parent_run_id = parent_run_id
        self.path = trace_dir / f"{run_id}.jsonl"
        trace_dir.mkdir(parents=True, exist_ok=True)

    def _base(self, event_type: str) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "run_id": self.run_id,
            "parent_run_id": self.parent_run_id,
            "event_type": event_type,
            "timestamp": utc_timestamp(),
        }

    def write(self, event_type: str, fields: dict[str, Any]) -> None:
        if event_type == "run_finished" and fields.get("status") not in RUN_FINISHED_STATUSES:
            raise ValueError(f"Invalid run_finished status: {fields.get('status')}")
        event = self._base(event_type)
        event.update(fields)
        redacted = _redact_jsonable(event)
        with self.path.open("a", encoding="utf-8", buffering=1) as handle:
            handle.write(json.dumps(redacted, sort_keys=True, default=str) + "\n")

    def run_started(self, *, input_hash: str, config_snapshot: dict[str, Any], question: str) -> None:
        self.write(
            "run_started",
            {
                "input_hash": input_hash,
                "config_snapshot": config_snapshot,
                "question": question,
            },
        )

    def llm_call(
        self,
        *,
        provider: str,
        model_id: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
        input_summary: str,
        output_summary: str,
    ) -> None:
        self.write(
            "llm_call",
            {
                "provider": provider,
                "model_id": model_id,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost_usd": cost_usd,
                "input_summary_redacted": input_summary,
                "output_summary_redacted": output_summary,
            },
        )

    def tool_call(
        self,
        *,
        tool_name: str,
        arguments: dict[str, Any],
        status: str,
        output_sample: Any,
        output_sample_strategy: str,
        output_sample_size: int,
        redacted_columns: list[str] | None = None,
        error: str | None = None,
    ) -> None:
        self.write(
            "tool_call",
            {
                "tool_name": tool_name,
                "arguments_redacted": arguments,
                "status": status,
                "output_sample_redacted": output_sample,
                "output_sample_strategy": output_sample_strategy,
                "output_sample_size": output_sample_size,
                "redacted_columns": redacted_columns or [],
                "error": error,
            },
        )

    def run_finished(
        self,
        *,
        status: str,
        steps: int,
        total_input_tokens: int,
        total_output_tokens: int,
        total_cost_usd: float,
        error: str | None,
    ) -> None:
        self.write(
            "run_finished",
            {
                "status": status,
                "steps": steps,
                "total_input_tokens": total_input_tokens,
                "total_output_tokens": total_output_tokens,
                "total_cost_usd": total_cost_usd,
                "error": error,
            },
        )
