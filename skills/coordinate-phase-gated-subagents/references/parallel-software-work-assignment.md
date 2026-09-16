# Assign independent software work to concurrent subagents

Partitioning here assigns independent software modules, files, tests, or
diagnostics to subagents. It does not mean partitioning production databases or
changing application architecture. Every assignment identifies allowed write
paths, source revision, prerequisites, and the evidence the worker must return.

Parallelism is safe only where work can be partitioned without hidden mutable
coupling.

## Build the dependency graph first

Represent implementation units as nodes. Add edges for required interfaces,
generated artifacts, schema/data ownership, shared global state, build-order
constraints, or source files that cannot be edited independently.

Run concurrently only nodes whose dependencies are satisfied and whose write
sets do not overlap.

## Preferred independent-work boundaries

Prefer, in order:

1. independent packages/crates/modules with stable interfaces;
1. disjoint source files with no generated-file collision;
1. independent platform backends;
1. independent test groups or diagnostic queues;
1. finer function-level work partitions only when file-level integration is
   serialized.

Avoid partitioning software work by arbitrary line ranges, error counts, or
equal file counts when dependency structure says otherwise.

## Ownership ledger

The orchestrator tracks for every active worker:

- work item;
- role;
- owned write paths;
- read dependencies;
- workspace/worktree;
- base revision;
- expected handoff;
- status.

Two active implementers must not own the same mutable path unless the agent host
provides transactional merging and the project explicitly relies on it.

## Scaling rule

Increase concurrency only after a representative trial demonstrates:

- workers understand the frozen artifacts;
- collision rate is low;
- review findings are actionable;
- integration cost does not dominate throughput;
- compute/I/O/build capacity is sufficient.

More agents can amplify a wrong instruction faster than they amplify correct
work. Fix the shared instruction before scaling.
