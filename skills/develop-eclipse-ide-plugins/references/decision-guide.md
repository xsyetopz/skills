# Decision guide

Use this guide after inspecting the target repository and current request. It
selects an evidence path; it does not grant permission for writes or external
operations.

| Condition | Action | Do not substitute |
| --- | --- | --- |
| Long work initiated by UI | Run as Job with cancellation/progress; marshal minimal UI update. | Blocking SWT thread. |
| Workspace resources are mutated | Use appropriate workspace operation/scheduling rule. | Uncoordinated filesystem write. |
| UI resource has finite owner | Dispose with owner; use JFace resource registries where suitable. | Per-paint allocations or global leak. |
| API differs across targets | Use declared target API or explicit supported compatibility path. | Compile newest and hope. |
| Headless logic is separable | Test core in JVM plus PDE integration for host boundary. | Only mocked host tests. |
| Distribution requested | Build feature/repository and install into clean target. | Bundle JAR alone. |

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
