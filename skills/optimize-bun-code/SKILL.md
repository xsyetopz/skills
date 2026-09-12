---
name: optimize-bun-code
description: >-
  Profile, review, or optimize Bun application performance using
  JavaScriptCore, allocation, memory, and native-API evidence. Use when Bun
  runtime speed, latency, throughput, allocation, or memory is the requested
  outcome; not for Bun upgrades or browser-only and Node-only tuning.
---

# Optimize Bun Code

Select this workflow automatically when the task matches its description.
Selection supplies guidance only; it does not authorize operations beyond the
user's request.

Define the workload and claim: startup, CPU cost, retention, throughput, or
latency. Measure a baseline before optimizing. Select the changed path from
profiles or measured workload frequency.

Read [measurement and memory][ref-1] for CPU/heap commands, JSC warm-up,
retainers, and RSS. Read [native APIs and concurrency][ref-2] for files, byte
ownership, streaming, workers, and bounded queues.

Remove measured redundant work, allocations, copies, or expensive calls.
Maintain error, ordering, encoding, lifetime, streaming, and cancellation
contracts. Account for backing-store retention when replacing copies with views.

Compare repeated before/after runs with identical runtime, build, inputs, and
hardware conditions. Run correctness checks for changed behavior. Report
distributions, errors, and measurement scope. Label unmeasured proposals as
hypotheses.

Use the [runnable RED/GREEN benchmark](assets/benchmark-repro/README.md) when a
small same-workload fixture helps demonstrate the distinction between a
plausible candidate and a locally measured result.

[ref-1]: references/measurement-and-memory.md
[ref-2]: references/native-apis-and-concurrency.md
