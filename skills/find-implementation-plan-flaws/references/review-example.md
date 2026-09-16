# Review a plan by following a concrete execution

Synthetic proposal: “Read the current config, merge requested changes, write the
file. Retry on failure.” Existing constraint: simultaneous edits by another tool
must not be lost; malformed input must leave the existing file unchanged.

Finding 1 — Lost update: the plan reads version A and writes an edited copy
after another writer has published version B. The success path overwrites B. Ask
for the actual version/locking contract and a stale-write check at publication,
not an unspecified “concurrency-safe implementation”. Test by holding the writer
between read and publication and replacing the input through a second writer.

Finding 2 — Destructive failure: opening the destination for truncation before
serialization finishes can destroy valid input. The plan needs complete parse
and validation before publication and an output-write strategy consistent with
the filesystem's actual guarantees. Test malformed input and injected
serialization failure. Do not claim crash durability just from an atomic rename.

Finding 3 — Retry changes meaning: an unconditional retry can apply a
non-idempotent change twice or overwrite a newly edited file. Specify which
failure is retryable, what is re-read, and which operation's effect can repeat.
A retry count alone does not answer those questions.

Review output: the violated constraint, exact step, concrete counterexample,
minimal necessary correction and verification. Label optional improvements
separately. Do not replace the user's plan with a larger architecture unless the
counterexample makes that boundary necessary. A plan's length, diagram count or
stage labels are not evidence that its dependencies are correct.
