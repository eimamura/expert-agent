from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from pathlib import Path
import signal
import threading
from typing import Any, Protocol

from agents.prompts import SYSTEM_PROMPT_TEMPLATE
from runtime.config import domain_path, knowledge_path, load_allowed_tables, runtime_snapshot, resolve_model_id
from runtime.cost import CostTracker, estimate_call_cost_usd
from runtime.fts_backend import SqliteFtsBackend
from runtime.formatter import ensure_response_format
from runtime.hashing import compute_input_hash, sha256_text, stable_json_dumps
from runtime.ids import new_run_id
from runtime.knowledge_loader import build_knowledge_index, read_knowledge_file, search_knowledge_files
from runtime.naive_backend import NaiveBackend
from runtime.provider_double import ScriptedProviderTimeout
from runtime.redaction import redact_jsonable
from runtime.search_backend import SearchBackend
from runtime.state import AgentState
from runtime.trace import TraceWriter
from tools.sql import get_table_schema, list_tables, run_readonly_sql


class LlmProvider(Protocol):
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
        ...


TOOL_SCHEMAS = [
    {
        "name": "search_knowledge",
        "description": "Search the knowledge base by keyword. Returns ranked file names and snippets. Use this before read_knowledge_file when you are not sure which file to read.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
    {
        "name": "read_knowledge_file",
        "description": "Read a Markdown knowledge file by relative path.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
    },
    {
        "name": "list_tables",
        "description": "List approved database tables visible to the read-only connection.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_table_schema",
        "description": "Get schema metadata for an approved schema-qualified table.",
        "input_schema": {
            "type": "object",
            "properties": {"table_name": {"type": "string"}},
            "required": ["table_name"],
        },
    },
    {
        "name": "run_readonly_sql",
        "description": "Run a parser-validated read-only SELECT query against approved tables.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
]


class AnthropicProvider:
    def __init__(self) -> None:
        import anthropic

        self.client = anthropic.Anthropic()

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
        response = self.client.messages.create(
            model=model_id,
            max_tokens=max_output_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=messages,
            tools=tools,
        )
        content: list[dict[str, Any]] = []
        for block in response.content:
            block_type = getattr(block, "type", None)
            if block_type == "text":
                content.append({"type": "text", "text": block.text})
            elif block_type == "tool_use":
                content.append(
                    {
                        "type": "tool_use",
                        "id": block.id,
                        "name": block.name,
                        "input": block.input,
                    }
                )
        usage = getattr(response, "usage", None)
        return {
            "content": content,
            "stop_reason": getattr(response, "stop_reason", None),
            "usage": {
                "input_tokens": int(getattr(usage, "input_tokens", 0) or 0),
                "output_tokens": int(getattr(usage, "output_tokens", 0) or 0),
            },
        }


def _tool_schema_identifiers() -> list[str]:
    return [f"{tool['name']}:{sha256_text(stable_json_dumps(tool['input_schema']))}" for tool in TOOL_SCHEMAS]


def _config_hash(path: Path) -> str:
    return sha256_text(path.read_text(encoding="utf-8")) if path.exists() else ""


def build_input_hash_parts(
    *,
    question: str,
    config_snapshot: dict[str, Any],
    knowledge_files: list[dict[str, Any]],
    allowed_tables: set[str],
) -> dict[str, Any]:
    return {
        "question": question,
        "system_prompt_template": SYSTEM_PROMPT_TEMPLATE,
        "knowledge_files": [{"path": item["path"], "sha256": item["sha256"]} for item in knowledge_files],
        "config_snapshot": config_snapshot,
        "tool_schema_identifiers": _tool_schema_identifiers(),
        "allowed_table_hash": sha256_text(stable_json_dumps(sorted(allowed_tables))),
        "redaction_config_hash": _config_hash(domain_path(config_snapshot, "rules", "redaction.yml")),
        "provider": config_snapshot["llm"]["provider"],
        "model_id": config_snapshot["llm"]["model_id"],
    }


def _execute_tool(
    name: str,
    args: dict[str, Any],
    config: dict[str, Any],
    backend: SearchBackend | None = None,
) -> Any:
    if name == "search_knowledge":
        if backend is None:
            raise ValueError("search_knowledge requires a search backend")
        top_n = int(config["knowledge"].get("index_top_n", 10))
        results = search_knowledge_files(backend, args["query"], top_n)
        return {"results": results}
    if name == "read_knowledge_file":
        return {
            "path": args["path"],
            "content": read_knowledge_file(
                knowledge_path(config),
                args["path"],
                int(config["knowledge"]["max_file_read_bytes"]),
            ),
        }
    if name == "list_tables":
        return {"tables": list_tables()}
    if name == "get_table_schema":
        return get_table_schema(args["table_name"])
    if name == "run_readonly_sql":
        return run_readonly_sql(args["query"])
    raise ValueError(f"Unknown tool: {name}")


def _normalize_error(error_type: str, message: str, retryable: bool, source: str) -> dict[str, Any]:
    return {
        "type": error_type,
        "message": message,
        "retryable": retryable,
        "source": source,
    }


def _truncate_tool_result(value: Any, max_bytes: int) -> tuple[Any, bool, int]:
    encoded = json.dumps(value, default=str)
    observed_size = len(encoded.encode("utf-8"))
    if observed_size <= max_bytes:
        return value, False, observed_size
    return {"truncated": True, "preview": encoded[:max_bytes]}, True, observed_size


def _run_with_timeout(callable_: Any, timeout_seconds: int, timeout_message: str) -> Any:
    if threading.current_thread() is threading.main_thread() and hasattr(signal, "SIGALRM"):
        previous_handler = signal.getsignal(signal.SIGALRM)

        def handler(signum: int, frame: Any) -> None:
            raise TimeoutError(timeout_message)

        signal.signal(signal.SIGALRM, handler)
        signal.setitimer(signal.ITIMER_REAL, timeout_seconds)
        try:
            return callable_()
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, previous_handler)

    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(callable_)
    try:
        return future.result(timeout=timeout_seconds)
    except FutureTimeoutError as exc:
        future.cancel()
        raise TimeoutError(timeout_message) from exc
    finally:
        executor.shutdown(wait=False, cancel_futures=True)


def _call_provider_with_timeout(provider: LlmProvider, timeout_seconds: int, **kwargs: Any) -> dict[str, Any]:
    return _run_with_timeout(
        lambda: provider.call(**kwargs),
        timeout_seconds,
        f"Provider call exceeded {timeout_seconds} seconds",
    )


def _execute_tool_with_timeout(
    name: str,
    args: dict[str, Any],
    config: dict[str, Any],
    backend: SearchBackend | None = None,
) -> Any:
    timeout_seconds = int(config["runtime"]["tool_timeout_seconds"])
    return _run_with_timeout(
        lambda: _execute_tool(name, args, config, backend),
        timeout_seconds,
        f"Tool call exceeded {timeout_seconds} seconds",
    )


def _validate_provider_response(response: dict[str, Any]) -> None:
    if not isinstance(response, dict):
        raise ValueError("Provider response must be a mapping")
    content = response.get("content")
    if not isinstance(content, list):
        raise ValueError("Provider response content must be a list")
    usage = response.get("usage", {})
    if not isinstance(usage, dict):
        raise ValueError("Provider response usage must be a mapping")
    for key in ("input_tokens", "output_tokens"):
        if key not in usage:
            raise ValueError(f"Provider response usage missing {key}")
    for block in content:
        if not isinstance(block, dict) or "type" not in block:
            raise ValueError("Provider response content blocks must include type")


def run_agent(
    question: str,
    config: dict[str, Any],
    provider: LlmProvider | None = None,
    run_id: str | None = None,
) -> AgentState:
    model_id, model_alias = resolve_model_id(config["llm"])
    snapshot = runtime_snapshot(config)
    search_backend_type = config["knowledge"].get("search_backend", "naive")
    top_n = int(config["knowledge"].get("index_top_n", 10))
    kpath = knowledge_path(config)
    if search_backend_type == "sqlite_fts":
        fts_db_path = Path(config["knowledge"].get("fts_db_path", "knowledge_index.db"))
        backend: SearchBackend = SqliteFtsBackend(kpath, fts_db_path)
    else:
        backend = NaiveBackend(kpath)
    knowledge_index, knowledge_files = build_knowledge_index(kpath, backend=backend, top_n=top_n)
    allowed_tables = load_allowed_tables(config)
    input_hash = compute_input_hash(
        build_input_hash_parts(
            question=question,
            config_snapshot=snapshot,
            knowledge_files=knowledge_files,
            allowed_tables=allowed_tables,
        )
    )
    state = AgentState(
        run_id=run_id or new_run_id(),
        parent_run_id=None,
        input_hash=input_hash,
        config_snapshot=snapshot,
    )
    trace = TraceWriter(Path(config["trace"]["dir"]), state.run_id, state.parent_run_id)
    trace.run_started(input_hash=input_hash, config_snapshot=snapshot, question=question)

    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(KNOWLEDGE_INDEX=knowledge_index)
    state.messages.append({"role": "user", "content": question})
    provider = provider or AnthropicProvider()
    costs = CostTracker(
        max_total_tokens=int(config["runtime"]["max_total_tokens"]),
        max_run_cost_usd=float(config["runtime"]["max_run_cost_usd"]),
    )

    try:
        while state.steps < int(config["runtime"]["max_steps"]):
            state.steps += 1
            response = _call_provider_with_timeout(
                provider,
                int(config["runtime"]["provider_timeout_seconds"]),
                system_prompt=system_prompt,
                messages=state.messages,
                tools=TOOL_SCHEMAS,
                model_id=model_id,
                max_output_tokens=int(config["runtime"]["max_output_tokens_per_call"]),
                temperature=float(config["llm"].get("temperature", 0)),
            )
            _validate_provider_response(response)
            usage = response.get("usage", {})
            input_tokens = int(usage.get("input_tokens", 0))
            output_tokens = int(usage.get("output_tokens", 0))
            call_cost = estimate_call_cost_usd(
                model_id,
                input_tokens,
                output_tokens,
                config["pricing"],
                model_alias=model_alias,
            )
            costs.add_call(input_tokens, output_tokens, call_cost)
            state.total_input_tokens = costs.total_input_tokens
            state.total_output_tokens = costs.total_output_tokens
            state.total_cost_usd = costs.total_cost_usd
            content = response.get("content", [])
            text_summary = "\n".join(block.get("text", "") for block in content if block.get("type") == "text")
            trace.llm_call(
                provider=config["llm"]["provider"],
                model_id=model_id,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=call_cost,
                input_summary=f"{len(state.messages)} messages",
                output_summary=text_summary[:2000],
            )
            exceeded = costs.exceeded_status()
            if exceeded:
                state.final_status = exceeded
                state.error = _normalize_error(
                    "budget_error",
                    f"Run stopped after exceeding {exceeded}",
                    False,
                    "budget",
                )
                state.limit_metadata = {
                    "max_total_tokens": int(config["runtime"]["max_total_tokens"]),
                    "max_run_cost_usd": float(config["runtime"]["max_run_cost_usd"]),
                    "observed_total_tokens": state.total_input_tokens + state.total_output_tokens,
                    "observed_total_cost_usd": state.total_cost_usd,
                }
                state.final_answer = ensure_response_format(text_summary)
                break

            tool_uses = [block for block in content if block.get("type") == "tool_use"]
            state.messages.append({"role": "assistant", "content": content})
            if not tool_uses:
                state.final_answer = ensure_response_format(text_summary)
                state.final_status = "success"
                break

            tool_results = []
            for tool_use in tool_uses:
                name = tool_use["name"]
                args = tool_use.get("input") or {}
                try:
                    result = _execute_tool_with_timeout(name, args, config, backend)
                    result, oversized, observed_size = _truncate_tool_result(
                        result, int(config["runtime"]["max_tool_result_bytes"])
                    )
                    result = redact_jsonable(result)
                    status = "success"
                    error = None
                    redacted_columns = result.get("redacted_columns", []) if isinstance(result, dict) else []
                except TimeoutError as exc:
                    result = redact_jsonable({"error": str(exc)})
                    oversized = False
                    observed_size = len(json.dumps(result, default=str).encode("utf-8"))
                    status = "error"
                    error = _normalize_error("timeout_error", str(exc), True, "tool")
                    redacted_columns = []
                    state.final_status = "timeout_error"
                except Exception as exc:
                    result = redact_jsonable({"error": str(exc)})
                    oversized = False
                    observed_size = len(json.dumps(result, default=str).encode("utf-8"))
                    status = "error"
                    error = _normalize_error("tool_error", str(exc), False, "tool")
                    redacted_columns = []
                    state.final_status = "tool_error"
                state.tool_calls.append({"tool_name": name, "arguments": args, "status": status})
                trace.tool_call(
                    tool_name=name,
                    arguments=args,
                    status=status,
                    output_sample=result,
                    output_sample_strategy=config["trace"]["output_sample_strategy"],
                    output_sample_size=int(config["trace"]["output_sample_size"]),
                    redacted_columns=redacted_columns,
                    error=error,
                    tool_result_truncated=oversized,
                    max_tool_result_bytes=int(config["runtime"]["max_tool_result_bytes"]),
                    observed_tool_result_bytes=observed_size,
                )
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_use.get("id", name),
                        "content": json.dumps(result, default=str),
                        "is_error": status == "error",
                    }
                )
                if oversized:
                    state.tool_calls[-1]["truncated"] = True
                    state.tool_calls[-1]["observed_tool_result_bytes"] = observed_size
            if state.final_status == "tool_error":
                state.error = _normalize_error("tool_error", "Tool execution failed", False, "tool")
                state.final_answer = ensure_response_format("A tool failed before a final answer was produced.")
                break
            if state.final_status == "timeout_error":
                state.error = _normalize_error("timeout_error", "Tool execution timed out", True, "tool")
                state.final_answer = ensure_response_format("A tool timed out before a final answer was produced.")
                break
            state.messages.append({"role": "user", "content": tool_results})
        else:
            state.final_status = "max_steps_exceeded"
            state.error = _normalize_error("budget_error", "Run stopped after max steps", False, "budget")
            state.limit_metadata = {
                "max_steps": int(config["runtime"]["max_steps"]),
                "observed_steps": state.steps,
            }
            state.final_answer = ensure_response_format(state.final_answer)
    except (TimeoutError, ScriptedProviderTimeout) as exc:
        state.final_status = "timeout_error"
        state.error = _normalize_error("timeout_error", str(exc), True, "provider")
        state.final_answer = ensure_response_format("The provider timed out before a final answer was produced.")
    except ValueError as exc:
        state.final_status = "validation_error"
        state.error = _normalize_error("validation_error", str(exc), False, "validator")
        state.final_answer = ensure_response_format("The provider returned an invalid response.")
    except Exception as exc:
        state.final_status = "llm_error"
        state.error = _normalize_error("provider_error", str(exc), False, "provider")
        state.final_answer = ensure_response_format("The LLM call failed before a final answer was produced.")
    finally:
        trace.run_finished(
            status=state.final_status,
            steps=state.steps,
            total_input_tokens=state.total_input_tokens,
            total_output_tokens=state.total_output_tokens,
            total_cost_usd=state.total_cost_usd,
            error=state.error,
            limit_metadata=state.limit_metadata,
        )
    return state
