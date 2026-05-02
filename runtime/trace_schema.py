from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, field_validator

from runtime.trace import RUN_FINISHED_STATUSES, SCHEMA_VERSION


class TraceSchemaError(ValueError):
    pass


class CommonEvent(BaseModel):
    model_config = ConfigDict(extra="allow")

    schema_version: Literal["1.0"]
    run_id: str
    parent_run_id: str | None = None
    event_type: str
    timestamp: str

    @field_validator("timestamp")
    @classmethod
    def validate_utc_timestamp(cls, value: str) -> str:
        if not value.endswith("Z"):
            raise ValueError("timestamp must be UTC and end with Z")
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("timestamp must be valid ISO 8601") from exc
        if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
            raise ValueError("timestamp must be UTC")
        return value


class NormalizedError(BaseModel):
    type: Literal[
        "provider_error",
        "tool_error",
        "validation_error",
        "timeout_error",
        "budget_error",
        "internal_error",
    ]
    message: str
    retryable: bool
    source: Literal["provider", "tool", "runtime", "validator", "budget", "unknown"]


class RunStartedEvent(CommonEvent):
    event_type: Literal["run_started"]
    input_hash: str
    config_snapshot: dict[str, Any]
    question: str


class LlmCallEvent(CommonEvent):
    event_type: Literal["llm_call"]
    provider: str
    model_id: str
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    cost_usd: float = Field(ge=0)
    input_summary_redacted: str
    output_summary_redacted: str


class ToolCallEvent(CommonEvent):
    event_type: Literal["tool_call"]
    tool_name: str
    arguments_redacted: dict[str, Any]
    status: Literal["success", "error"]
    output_sample_redacted: Any
    output_sample_strategy: str
    output_sample_size: int = Field(ge=0)
    redacted_columns: list[str]
    error: NormalizedError | None = None
    tool_result_truncated: bool = False
    max_tool_result_bytes: int | None = None
    observed_tool_result_bytes: int | None = None


class RunFinishedEvent(CommonEvent):
    event_type: Literal["run_finished"]
    status: str
    steps: int = Field(ge=0)
    total_input_tokens: int = Field(ge=0)
    total_output_tokens: int = Field(ge=0)
    total_cost_usd: float = Field(ge=0)
    error: NormalizedError | None = None
    limit_metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        if value not in RUN_FINISHED_STATUSES:
            raise ValueError(f"invalid run_finished status: {value}")
        return value


TraceEvent = Union[RunStartedEvent, LlmCallEvent, ToolCallEvent, RunFinishedEvent]
_EVENT_ADAPTER = TypeAdapter(TraceEvent)


def validate_trace_event(event: dict[str, Any]) -> TraceEvent:
    if event.get("schema_version") != SCHEMA_VERSION:
        raise TraceSchemaError("unsupported or missing schema_version")
    event_type = event.get("event_type")
    if event_type not in {"run_started", "llm_call", "tool_call", "run_finished"}:
        raise TraceSchemaError(f"unsupported event_type: {event_type}")
    try:
        return _EVENT_ADAPTER.validate_python(event)
    except Exception as exc:
        raise TraceSchemaError(str(exc)) from exc


def validate_trace_events(events: list[dict[str, Any]]) -> list[TraceEvent]:
    validated = [validate_trace_event(event) for event in events]
    if not any(event.event_type == "run_finished" for event in validated):
        raise TraceSchemaError("trace is missing run_finished event")
    return validated
