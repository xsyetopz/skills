# Operational decisions for Phase Gated Delivery

Use this guide after inspecting the request and target system for multi-agent
phase coordination. It selects an evidence path; it does not grant permission
for an external write or another consequential operation.

| Condition | Action | Do not substitute |
| --- | --- | --- |
| Task is simple or tightly coupled | Use one agent; retain the phase discipline only if explicitly requested. | Subagents created merely because capacity exists. |
| Read-only investigations are independent | Run them in parallel with shared context and distinct questions. | Duplicate reconnaissance with no replication purpose. |
| Two implementation items touch the same files or invariant | Serialize them or assign one owner and one read-only reviewer. | Concurrent conflicting writes. |
| One child reports a surprising design change | Treat it as a proposal; inspect evidence and route through the appropriate earlier phase. | Adopting it because the child sounds confident. |
| One independent review covers the material risk | Use it and integrate findings. | Additional reviewers that repeat the same checklist. |
| A phase check cannot run | Record unavailable and decide whether the phase may remain blocked or the user accepts a narrower deliverable. | Marking it passed or substituting an unrelated green check. |

## Unresolved decisions

A material scope, compatibility, interface, deployment, or policy choice for the
multi-agent phase coordination remains user-owned when repository evidence does
not settle it. Present concrete alternatives and consequences. Resolve routine
internal details that do not change an external contract.

## Avoiding false precision

Use thresholds, limits, versions, and acceptance criteria that govern the
multi-agent phase coordination. If none exists, report measurements or
uncertainty. Do not invent a timeout, reviewer count, confidence score, target,
or error budget and then treat it as a requirement.
