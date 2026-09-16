# Decision guide

Use this guide after inspecting the target repository and current request. It
selects an evidence path; it does not grant permission for writes or external
operations.

| Condition | Action | Do not substitute |
| --- | --- | --- |
| Task is simple or tightly coupled | Use one agent; retain the phase discipline only if explicitly requested. | Subagents created merely because capacity exists. |
| Read-only investigations are independent | Run them in parallel with shared context and distinct questions. | Duplicate reconnaissance with no replication purpose. |
| Two implementation items touch the same files or invariant | Serialize them or assign one owner and one read-only reviewer. | Concurrent conflicting writes. |
| One child reports a surprising design change | Treat it as a proposal; inspect evidence and route through the appropriate earlier phase. | Adopting it because the child sounds confident. |
| One independent review covers the material risk | Use it and integrate findings. | Additional reviewers that repeat the same checklist. |
| A phase check cannot run | Record unavailable and decide whether the phase may remain blocked or the user accepts a narrower deliverable. | Marking it passed or substituting an unrelated green check. |

## Unresolved decisions

A material product, compatibility, public-interface, deployment, or policy
choice remains user-owned when repository evidence does not settle it. Present
the concrete alternatives and consequences. Routine implementation details that
do not change an external contract remain the agent's responsibility.

## Avoiding false precision

Use project-defined thresholds, limits, versions, and acceptance criteria. When
none exists, report measurements or uncertainty; do not invent a timeout,
reviewer count, confidence score, supported version, performance target, or
error budget and then treat it as a requirement.
