# Operate Scala performance changes at fleet scale

A locally faster candidate can regress another target, increase memory, or
invalidate an operational contract. Use staged rollout when the optimized path
serves production traffic or distributed artifacts. Do not create a new release
or approval system when the repository already defines one.

## Control matrix

| Control | Required record | Observable failure |
| --- | --- | --- |
| Reproducible baseline | Source revision, Scala/compiler version, JVM/JS/Native backend, JDK/runtime flags, GC, dependencies, build settings, architecture, and workload, hardware/OS, dependency lock, fixture identity, raw measurements. | A later operator cannot reconstruct the compared binaries or workload. |
| Compatibility matrix | supported Scala versions/backends, JDK/runtime matrix, compiler flags, binary compatibility, GC/container settings, dependencies, architecture, and rollback artifact. | Candidate succeeds only on the profiling host or unsupported feature set. |
| Budget tradeoffs | CPU, latency distribution, throughput, allocations, retained memory, code size/startup, and operational cost relevant to the goal. | One metric improves while a required budget silently regresses. |
| Staged exposure | Existing canary/cohort mechanism, comparable telemetry, stop threshold from policy, and rollback owner. | Full rollout occurs before production-shaped evidence exists. |
| Artifact identity | Exact built artifact, profile symbols, configuration, and promoted revision. | Validation and deployment use different binaries or settings. |

## Rollout verification

Run the target matrix before promotion. Compare the same service-level metric
and guard metrics before and after exposure. Verify the predicted
profile/counter change on a representative target. Use the established rollback
when a guard metric violates its existing threshold; do not invent a new
threshold after seeing the result. Retain benchmark data and profiles according
to repository policy, and keep confidential workload data in approved systems.
