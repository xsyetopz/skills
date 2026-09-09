---
name: bun-performance
description:
  Profile, review, or optimize Bun application performance using JavaScriptCore,
  allocation, memory, and native-API evidence. Excludes Bun upgrades and
  browser-only or Node-only tuning.
---

# Bun Performance

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

[ref-1]: references/measurement-and-memory.md
[ref-2]: references/native-apis-and-concurrency.md
