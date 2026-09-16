# Map software subagent roles to the agent host’s tools

The agent host is the CLI, IDE, or service that creates independent subagent
contexts and exposes coordination tools. The orchestrator assigns software work
and collects results through those actual tools. The conceptual calls below are
pseudocode, not executable APIs or a request to build a wrapper.

Use agent-host-native primitives. This skill defines roles and information flow,
not API names or a provider-specific orchestration language.

## Inspect host capabilities

Map these operations to actual host support. Independent contexts and result
identity are required for independent multi-agent work; serialize tasks when
parallel execution is unavailable:

| Capability | Required behavior |
| --- | --- |
| Spawn | Create a subagent with an isolated reasoning/context state. |
| Scope | Give a worker only the task, frozen artifacts, owned paths, and tools it needs. |
| Wait | Obtain a terminal result or explicit failure/timeout. |
| Identify | Associate every result with a unique work item and role. |
| Parallelize | Run independent workers concurrently without sharing mutable state unsafely. |
| Cancel | Stop obsolete or invalidated work after a baseline/change decision. |

If the host lacks a capability, state the actual limit. Short task wording does
not enforce a deadline. Use native cancellation/deadlines when available.
Without cancellation, isolate writes, reject invalidated results, and wait for
terminal state before allowing conflicting work. Do not claim termination from a
stop request or abandon a worker that can still mutate shared state.

Read the effective runtime model, permissions, and tool assignment when the host
exposes them. Requested overrides that cannot be applied must be reported, not
silently dropped. Close/release completed contexts after consuming their results
when the host requires explicit cleanup.

## Generic orchestration vocabulary

Use these conceptual verbs in plans and translate them to the host:

```text
spawn(role, task, context, owned_paths) -> worker_id
wait(worker_id) -> result
spawn_many(work_items) -> worker_ids
wait_all(worker_ids) -> results
cancel(worker_id, reason)
```

Do not invent a compatibility wrapper in the user's repository merely to make
these names real.

## Context partitions

- **Orchestrator:** task authority, baselines, change log, dependency graph,
  phase completion check state, worker ownership.
- **Implementer:** one work item, relevant frozen requirements/design, source
  files, existing tests, allowed paths.
- **Independent defect-focused software reviewer:** diff/output under review,
  relevant contracts and acceptance criteria, test evidence. Exclude the
  implementer's private rationale unless the rationale itself is a deliverable.
- **Correction-and-integration agent:** accepted findings, original change,
  frozen contracts, owned paths, verification commands.
- **Verifier:** requirement-to-evidence matrix and executable system; no mandate
  to make implementation changes unless assigned a separate
  correction-and-integration agent task.

## Worker result contract

Every worker must return:

1. work-item identifier and role;
1. files/artifacts examined or changed;
1. concrete outcome;
1. commands/checks actually executed and results;
1. findings or blockers with evidence;
1. whether it stayed within owned scope;
1. commit/hash/path when the agent host uses versioned handoff.

Narrative confidence without evidence is not a usable result.
