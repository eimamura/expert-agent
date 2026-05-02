from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import BackgroundTasks, FastAPI, HTTPException
from pydantic import BaseModel

from app.main import load_dotenv
from runtime.config import load_config
from runtime.ids import new_run_id
from runtime.loop import run_agent
from runtime.redaction import redact_text
from runtime.run_store import RunStore
from runtime.trace_reader import load_validated_trace

app = FastAPI(title="Expert Agent API", version="3.0.0")

_config: dict[str, Any] = {}
_run_store: RunStore | None = None


def init(config_path: str = "config/app.yml", db_path: str = "runs.db") -> None:
    global _config, _run_store
    load_dotenv()
    _config = load_config(config_path)
    _run_store = RunStore(db_path)


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _run_in_background(run_id: str, question: str) -> None:
    store = _run_store
    config = _config
    if store is None or not config:
        return
    try:
        store.update_run(run_id, status="running")
        state = run_agent(question, config, run_id=run_id)
        error_type = state.error.get("type") if state.error else None
        error_message = state.error.get("message") if state.error else None
        store.update_run(
            run_id,
            status=state.final_status,
            finished_at=_now_utc(),
            total_input_tokens=state.total_input_tokens,
            total_output_tokens=state.total_output_tokens,
            total_cost_usd=state.total_cost_usd,
            final_answer=redact_text(state.final_answer) if state.final_answer else None,
            input_hash=state.input_hash,
            config_snapshot=state.config_snapshot,
            error_type=error_type,
            error_message=error_message,
        )
    except Exception as exc:
        store.update_run(
            run_id,
            status="llm_error",
            finished_at=_now_utc(),
            error_type="internal_error",
            error_message=str(exc),
        )


async def _schedule_run(run_id: str, question: str) -> None:
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, _run_in_background, run_id, question)


class CreateRunRequest(BaseModel):
    question: str
    config_overrides: dict[str, Any] = {}


class CreateRunResponse(BaseModel):
    run_id: str
    status: str


@app.post("/runs", response_model=CreateRunResponse, status_code=202)
async def create_run(
    body: CreateRunRequest, background_tasks: BackgroundTasks
) -> CreateRunResponse:
    if _run_store is None or not _config:
        raise HTTPException(status_code=503, detail="Service not initialized")
    run_id = new_run_id()
    redacted_question = redact_text(body.question)
    _run_store.create_run(
        run_id=run_id,
        question=redacted_question,
        input_hash="",
        config_snapshot={},
        created_at=_now_utc(),
    )
    background_tasks.add_task(_schedule_run, run_id, body.question)
    return CreateRunResponse(run_id=run_id, status="queued")


@app.get("/runs/{run_id}")
async def get_run(run_id: str) -> dict[str, Any]:
    if _run_store is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    run = _run_store.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    run.pop("config_snapshot", None)
    return run


@app.get("/runs/{run_id}/trace")
async def get_trace(run_id: str) -> dict[str, Any]:
    if _run_store is None or not _config:
        raise HTTPException(status_code=503, detail="Service not initialized")
    run = _run_store.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    trace_dir = Path(_config.get("trace", {}).get("dir", "traces"))
    trace_path = trace_dir / f"{run_id}.jsonl"
    if not trace_path.exists():
        raise HTTPException(status_code=404, detail="Trace not found")
    events = load_validated_trace(trace_path)
    return {"run_id": run_id, "events": [e.model_dump() for e in events]}
