# docs/phase_plans/phase5_implementation_plan.md

## Role

This document is the implementation plan for Phase 5: LangGraph workflow orchestration.

Phase 5 starts from the Phase 4 baseline once Phase 4 is released.

## Status

Phase 5 is not started.

## Objective

Introduce LangGraph as the workflow engine after the minimal custom loop behavior is proven stable. The custom loop in `runtime/loop.py` becomes the reference behavior that LangGraph must preserve.

Reference: `docs/07_future_scaling.md` § Phase 5.

---

## Trigger conditions

Phase 5 should be started when any of the following apply:

- The loop has several stable branches that are hard to maintain in plain Python
- Retries and state transitions become complex enough to need explicit graph nodes
- Multiple tools need structured routing logic
- Parent/child run semantics (sub-runs, delegation) become important
- Human approval steps are needed in the loop

---

## Scope

### New capabilities

- Replace `runtime/loop.py` custom loop with a LangGraph `StateGraph`
- Graph nodes map to current loop stages: `call_provider`, `execute_tools`, `check_limits`, `finalize`
- Edge conditions replace current `while` / `if` branching
- Parent/child run support via LangGraph's built-in thread/checkpoint model
- Human-in-the-loop approval step as an optional interrupt node
- Existing `AgentState` dataclass becomes LangGraph state schema

### Preserved from Phase 4

- Trace event schema `"1.0"` and `NormalizedError` shape
- Redaction before LLM input and trace persistence
- Budget tracking (steps, tokens, cost, timeouts)
- Provider test doubles interface
- Eval assertions and fixture traces
- `read_knowledge_file` and `search_knowledge` tool interface
- HTTP API (`app/api.py`) — no change to external contract
- CLI (`app/main.py`) — no change

### Out of scope in Phase 5

- Multi-agent orchestration across separate processes
- Web UI
- Write SQL tools
- New channel integrations (Phase 6)

---

## Migration policy

LangGraph must preserve all Phase 1–4 loop semantics:

- Redaction before LLM-visible tool results
- Redaction before trace persistence
- Max step, token, and cost limits enforced
- Trace event schema compatibility (`run_started`, `llm_call`, `tool_call`, `run_finished`)
- `input_hash` semantics unchanged
- Default tests must not require live LLM credentials

---

## Completion checklist

- [ ] Step 1: Add `langgraph` to dependencies.
- [ ] Step 2: Define LangGraph state schema from `runtime/state.py` `AgentState`.
- [ ] Step 3: Implement graph nodes (`call_provider`, `execute_tools`, `check_limits`, `finalize`) in `runtime/graph.py`.
- [ ] Step 4: Wire edges and conditional routing to match current loop behavior.
- [ ] Step 5: Replace `run_agent()` body in `runtime/loop.py` with LangGraph graph invocation; keep the function signature unchanged.
- [ ] Step 6: Verify all existing tests pass without modification (provider doubles must work with LangGraph nodes).
- [ ] Step 7: Add LangGraph-specific tests: node unit tests, interrupt/resume, parent/child run.
- [ ] Step 8: Update `docs/CURRENT_STATE.md`, `docs/baselines/README.md`, and this file.

---

## Guardrails inherited from Phase 4

- Preserve all Phase 1–4 trace and eval guardrails.
- `run_agent()` function signature must remain unchanged so `app/api.py` and `app/main.py` require no edits.
- Provider test doubles must remain compatible.
- No write SQL tools or unrestricted SQL.

---

## Implementation Result

**Status:** Pending

**Implemented files:**
- (To be filled on completion)

**Deviations from plan:**
- (To be filled on completion)
