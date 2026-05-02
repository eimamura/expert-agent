# ADR-0002: Defer LangGraph Until Phase 5

## Status

Accepted

## Context

LangGraph and workflow orchestration engines are powerful tools for complex multi-step agent flows. The question was whether to adopt LangGraph from the start or build a minimal custom loop first.

## Decision

Do not use LangGraph until Phase 5. Build a minimal direct loop in `runtime/loop.py` for Phases 1–4.

## Rationale

Phase 1–4 priorities are:

- Clear, debuggable control flow with no hidden state transitions
- Explicit trace records that are easy to validate
- Low implementation overhead — the custom loop fits in one file
- Proven runtime behavior before introducing an orchestration abstraction

LangGraph is the right tool once:

- the loop has several stable branches;
- retries and state transitions become complex;
- multiple tools need structured routing;
- parent/child run semantics become important;
- human approval steps are needed.

None of these conditions apply before Phase 5.

## Consequences

**Positive**

- The runtime loop remains fully auditable and traceable.
- Provider test doubles and eval assertions work against simple Python code, not a framework abstraction.
- Migration to LangGraph in Phase 5 is possible because the trace schema and guardrails are well-defined.

**Negative**

- Retry logic and branching must be hand-coded for Phases 1–4.
- The custom loop will not benefit from LangGraph's built-in state management.

## References

- `docs/01_architecture_principles.md` — Why not start with LangGraph
- `docs/07_future_scaling.md` § Phase 5 — LangGraph migration plan
- `runtime/loop.py` — current custom loop implementation
