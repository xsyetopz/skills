# Decision guide

Use this guide after inspecting the target repository and current request. It
selects an evidence path; it does not grant permission for writes or external
operations.

| Condition | Action | Do not substitute |
| --- | --- | --- |
| Packaged release reproduces issue | Capture release identity and isolate configuration before source build. | Immediate rebuild from unrelated head. |
| Only one renderer fails | Compare software/other backend and driver/settings; locate renderer path. | Calling it a guest bug. |
| Save state reproduces issue | Record creation revision/settings and also seek reproducible boot/path if portability matters. | Assuming state works across versions. |
| Patch changes guest behavior | Bind it to exact serial/CRC/version and verify conditions. | Generic addresses for all releases. |
| Unknown CLI setting requested | Check current upstream parser/options or use explicit passthrough. | Dropping it. |
| Build failure occurs | Inspect first compiler/link/dependency error and target configuration. | Changing guest settings. |

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
