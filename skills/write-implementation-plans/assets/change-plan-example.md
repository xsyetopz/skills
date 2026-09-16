# Worked change plan: replace an allocation-heavy delimiter counter

Illustrative plan for an already-specified exact delimiter count. This is not a
prescription to invent delivery stages for every task.

1. Locate the counter, its callers and existing expected-value tests. Confirm
   whether the delimiter is a byte, UTF-16 code unit, Unicode scalar or string.
   Preserve that definition and error behavior; do not silently substitute one.
1. Add boundary cases that distinguish counting from splitting: empty input,
   leading/trailing/adjacent delimiters, no match and non-ASCII data. Run them
   against the current implementation to establish the behavior being retained.
1. Capture the representative workload and baseline measurement with the
   existing existing benchmark framework. Record setup and result-consumption
   boundaries. No hardcoded speedup target is assumed when the request supplied
   none.
1. Change only the counter's implementation. Re-run the expected-value cases and
   the affected consumer test. Compare matched benchmark identities and sample
   variability; inspect allocation evidence separately from elapsed time.
1. Review the diff for changed contracts and unneeded specialization. Retain the
   candidate only if it meets the requested objective without unacceptable
   tradeoffs.

Dependencies: the delimiter contract precedes implementation; correctness
precedes interpreting performance; performance evidence precedes claiming a
speedup. No migration, queue, approval requirement, service or new package is
needed here.

Completion evidence: patch, named contract checks, exact benchmark commands and
results or explicit missing runtime/data. Unknown CI availability is not
permission to claim it passed. A failed comparison requires correcting the cause
or reporting an inconclusive result, not weakening the test.
