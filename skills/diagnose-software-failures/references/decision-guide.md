# Decision guide

Use this guide after inspecting the target repository and current request. It
selects an evidence path; it does not grant permission for writes or external
operations.

| Condition | Action | Do not substitute |
| --- | --- | --- |
| Failure is deterministic with small input | Reduce and instrument the first divergence. | Broad tracing of the whole system first. |
| Failure is intermittent or concurrent | Record frequency/conditions, use controlled scheduling or race tools, and repeat enough to separate chance. | Sleeps or one lucky pass. |
| Crash occurs after memory corruption | Use sanitizer/debugger/heap evidence and trace the earlier violation. | Fixing the final dereference only. |
| Hang may be deadlock or slow I/O | Inspect thread/task stacks, wait/ownership graph, and external I/O state. | Increasing timeout. |
| Build fails only incrementally | Compare clean and incremental dependency/generation state. | Declaring success from a clean build. |
| Regression range is known but cause is not | Use the failure oracle with Git bisect after it reliably classifies revisions. | Marking unbuildable revisions bad. |

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
