# ADR-0005: Skip Phase 5 (LangGraph) and Proceed Directly to Phase 6

## Status

Accepted — 2026-05-02

## Context

Phase 5 was planned as a migration of `runtime/loop.py` to a LangGraph `StateGraph`. The plan defined explicit trigger conditions before work should begin:

- The loop has several stable branches that are hard to maintain in plain Python
- Retries and state transitions become complex enough to need explicit graph nodes
- Multiple tools need structured routing logic
- Parent/child run semantics (sub-runs, delegation) become important
- Human approval steps are needed in the loop

After Phase 3 shipped (HTTP API + run persistence), the loop in `runtime/loop.py` is still a single straightforward `while` loop with one primary tool dispatch path. None of the trigger conditions have materialized.

## Decision

Skip Phase 5. Proceed directly from Phase 3 to Phase 6 (multiple channel integrations, Web UI first).

## Rationale

The Phase 5 trigger conditions were designed to prevent premature adoption of an orchestration abstraction. Evaluating the current state against each condition:

| Condition | Current state |
| --- | --- |
| Several stable loop branches | No — single tool dispatch path |
| Complex retry / state transitions | No — simple step limit + error handling |
| Multiple tools needing structured routing | No — tools are dispatched by name, no graph needed |
| Parent/child run semantics | No — single-run model, no sub-runs |
| Human approval steps | No — fully automated loop |

The practical need driving the next work is a usable Web UI, not loop complexity. Jumping to Phase 6 directly delivers concrete user value while the loop remains simple enough to maintain in plain Python.

Phase 5 is not cancelled — it is deferred until at least one trigger condition is met. The plan in `docs/phase_plans/phase5_implementation_plan.md` remains valid for future use.

## Consequences

**Positive**

- Phase 6 (Web UI) delivers usable tooling sooner.
- `runtime/loop.py` stays simple and auditable.
- No framework dependency introduced before it is needed.

**Negative**

- If loop complexity grows unexpectedly during Phase 6, a mid-phase refactor to LangGraph may be harder than a clean migration from Phase 5 would have been.

## References

- `docs/phase_plans/phase5_implementation_plan.md` — deferred plan with trigger conditions
- `docs/phase_plans/phase6_implementation_plan.md` — next active phase
- `docs/decisions/ADR-0002-no-langgraph-until-phase5.md` — original rationale for deferring LangGraph
- `runtime/loop.py` — current loop (still simple enough to skip Phase 5)
