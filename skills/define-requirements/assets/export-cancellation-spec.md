# Worked specification: cancel an unpublished export

Illustrative requirements, not facts about the user's system.

## Scope and existing constraints

A single-process service writes an export to a temporary file and then publishes
it by replacing its destination. Existing exports must not be deleted by a
cancel request. No distributed worker queue, new endpoint, or storage service is
introduced by this example. The destination is on the same filesystem as its
temporary file; cross-filesystem publication is outside this example's contract.

## Observable contract

| Before the operation | Event | Required observation |
| --- | --- | --- |
| Writing temporary output | Cancellation accepted before publication starts | No new destination is published. The job ends as cancelled; its owned temporary file is removed. Existing destination contents remain unchanged. |
| Writing temporary output | Validation fails | No destination is published. Report the validation error; clean only the job's temporary file. |
| Ready to publish | Cancellation competes with publication | A single state transition decides the winner. If publication wins, cancel reports that publication has started; it does not claim the effects were undone. |
| Published | Repeated cancellation | Published bytes remain. Return the existing completed outcome; do not convert it into cancelled. |
| Cancelled | Repeated cancellation | No new side effects; the outcome remains cancelled. |
| Any nonterminal state | Process dies | Recovery behavior is unresolved unless crash recovery is part of the actual request. Do not promise durability merely because rename is atomic. |

The publication decision is the linearization point for cancellation, not the
arrival time of a client packet. “Cancel requested” and “cancel accepted” are
different observations. An inability to remove temporary output must be reported
as cleanup failure without pretending publication occurred.

## Acceptance examples

Hold the writer at a test barrier before publication; accept cancellation;
release the writer. Assert unchanged destination bytes, terminal cancelled
status and absence of that job's temporary file. Repeat with publication already
committed: assert completed status and the new bytes survive cancellation.
Execute duplicate cancellation after each terminal state. Use a controlled
barrier, not a sleep.

## Decisions that need actual system evidence

Destination replacement semantics and permission handling; how callers observe
state; whether failures must survive restart; maximum output size; real latency
or throughput limits. Do not fill these with invented “industry standard”
values.
