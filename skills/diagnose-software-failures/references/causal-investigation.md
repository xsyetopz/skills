# Causal investigation without patch accumulation

Start from one exact observation: failing invocation, input identity, revision,
environment, error text and expected behavior. Capture the first error and its
causal stack, not only a wrapper's “build failed”. A change that removes the
message by swallowing an exception is not a fix.

## Distinguishing experiments

| Competing explanations | Useful discriminating observation | Misleading substitute |
| --- | --- | --- |
| Bad input versus parser regression | Same immutable bytes on known-good and bad revisions, with the same options | Manually retyping “equivalent” input |
| Allocations versus retention | Allocation trace plus live-object/retainer evidence after the same workload | A single process RSS reading |
| Deadlock versus slow external I/O | Thread/task stacks and ownership/wait graph, correlated with I/O state | Increasing timeout until the failure disappears |
| Race versus deterministic ordering error | Controlled schedule/barriers and assertions at the contested state transition | Adding sleeps or retrying until a test happens to pass |
| Cache invalidation versus source error | Named cold/warm runs with cache identity recorded | Deleting every cache and declaring the bug fixed |
| Missing runtime dependency versus source defect | Resolve the native loader/import error for the actual executable | Editing production code to bypass initialization |

Record a prediction before an experiment. An outcome that disagrees with the
prediction changes the hypothesis, not the expected-result check. Repeated edits
with the same failed prediction provide no new evidence. Re-read the relevant
boundary, check the assumptions and use a different discriminating observation.
There is no universal line-count or attempt-count limit.

Use a debugger, trace, reduced input, static proof, or test according to what
can observe the property. Agents are not limited to unit-test output. Never
claim a root cause from temporal correlation alone. A narrower statement such as
“reproduces only with these bytes on this revision” is preferable to a invented
architectural diagnosis.

When a hypothesis fails, undo only your attributable experimental changes. Do
not reset the entire working tree or overwrite the user's pre-existing edits.
Keep evidence that distinguishes the failed approach from the next one.
