# Extension design decisions for Eclipse OSGi Plugin

Use this guide after inspecting the request and target system for Eclipse
plugin. It selects an evidence path; it does not grant permission for an
external write or another consequential operation.

| Condition | Action | Do not substitute |
| --- | --- | --- |
| Long work initiated by UI | Run as Job with cancellation/progress; marshal minimal UI update. | Blocking SWT thread. |
| Workspace resources are mutated | Use appropriate workspace operation/scheduling rule. | Uncoordinated filesystem write. |
| UI resource has finite owner | Dispose with owner; use JFace resource registries where suitable. | Per-paint allocations or global leak. |
| API differs across targets | Use declared target API or explicit supported compatibility path. | Compile newest and hope. |
| Headless logic is separable | Test core in JVM plus PDE integration for host boundary. | Only mocked host tests. |
| Distribution requested | Build feature/repository and install into clean target. | Bundle JAR alone. |

## Unresolved decisions

A material scope, compatibility, interface, deployment, or policy choice for the
Eclipse plugin remains user-owned when repository evidence does not settle it.
Present concrete alternatives and consequences. Resolve routine internal details
that do not change an external contract.

## Avoiding false precision

Use thresholds, limits, versions, and acceptance criteria that govern the
Eclipse plugin. If none exists, report measurements or uncertainty. Do not
invent a timeout, reviewer count, confidence score, target, or error budget and
then treat it as a requirement.
