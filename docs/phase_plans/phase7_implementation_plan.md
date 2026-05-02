# docs/phase_plans/phase7_implementation_plan.md

## Role

This document is the implementation plan for Phase 7: agent platform.

Phase 7 starts from the Phase 6 baseline once Phase 6 is released.

## Status

Phase 7 is not started.

## Objective

Turn the project into a reusable internal agent platform only after the domain agent proves value. Phase 7 is intentionally vague until Phase 6 is complete — the exact shape of the platform will be driven by operational needs discovered in Phases 1–6.

Reference: `docs/07_future_scaling.md` § Phase 7.

---

## Trigger conditions

Phase 7 should be started only when:

- The subscription commerce domain agent is in active production use
- A second domain agent is requested
- Operational needs (cost controls, approval workflows, audit) justify platform investment

Do not start Phase 7 to speculate about future domains.

---

## Scope (provisional)

### Potential platform features

| Feature | Trigger |
| --- | --- |
| Multiple domain agents | Second domain requested |
| Shared tool registry | 3+ agents sharing the same tools |
| Shared policy registry | Cross-domain redaction or SQL policy needed |
| Centralized trace storage | JSONL files per domain become unmanageable |
| Approval workflows | Human-in-the-loop required before certain tool calls |
| User and tenant isolation | Multiple teams or customers using the platform |
| Evaluation dashboards | Automated eval quality reporting needed |
| Cost controls | Per-team or per-domain budget enforcement |
| Model routing | Different models for different agents or query types |

### Architecture policy

The platform layer must remain invisible to individual domain agents:

```
Domain agent  →  Platform runtime  →  Shared tools / policies / trace store
```

- Domain agents are still configured via YAML domain packs (`domains/[name]/`).
- The `run_agent()` interface is preserved; the platform wraps it, not replaces it.
- Trace schema `"1.0"` compatibility must be maintained or a formal migration run.

---

## Completion checklist

Checklist will be defined when Phase 6 is complete and platform requirements are known.

- [ ] Step 0: Audit operational pain points after Phase 6 ships — derive actual platform requirements.
- [ ] Step 1: (TBD based on Step 0 findings)

---

## Guardrails

- Do not design for hypothetical future domains.
- Do not introduce a platform abstraction before a second domain agent exists.
- Trace schema compatibility must be preserved or a versioned migration provided.
- No write SQL tools introduced by platform layer.

---

## Implementation Result

**Status:** Pending

**Implemented files:**
- (To be filled on completion)

**Deviations from plan:**
- (To be filled on completion)
