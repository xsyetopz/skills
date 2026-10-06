# Agent Failure Modes

Read when reviewing a diff that an agent wrote, or before submitting your own.
Agents write code that is plausible in one function and wrong for the repository.
Each entry gives the failure, how to spot it in a diff, and the fix.

## Contents

- [Local Optimization](#local-optimization)
- [Terminology Drift](#terminology-drift)
- [Over-Abstraction](#over-abstraction)
- [Under-Abstraction](#under-abstraction)
- [Guessing](#guessing)
- [Churn](#churn)
- [Tests as Proof](#tests-as-proof)
- [Imitating Bad Code](#imitating-bad-code)
- [Comments as Understanding](#comments-as-understanding)

## Local Optimization

- Failure: one function gets cleaner while the repository gets less coherent.
- Spot: a new helper layer, framework, or naming scheme; a pattern that no neighbor uses.
- Fix: read the neighboring files first and reuse their pattern.
  Keep the architecture unless the task changes it.

## Terminology Drift

- Failure: a synonym per prompt (`client` for `customer`, `store` for `repo`),
  or one name for two concepts.
- Spot: new identifiers whose terms differ from the `rg -c` counts of the existing ones.
- Fix: use the existing term.
  Rename only when the task is the rename.

## Over-Abstraction

- Failure: code extracted because two regions look alike, not because they share a concept.
- Spot: a class or helper with one caller,
  a wrapper that renames trivial syntax (`increment_index()`),
  an interface with one implementation.
- Fix: inline it.
  Extract only a stable concept, such as `validate_packet_header()`.

## Under-Abstraction

- Failure: one long procedure, because each next line was easy to generate.
- Spot: a function past the review limits in [readability](readability.md)
  with several purposes or abstraction levels.
- Fix: extract blocks that have their own purpose or invariant and a name clearer than a comment.
  Do not cut at arbitrary lines to meet a line count.

## Guessing

- Failure: missing knowledge becomes confident code:
  an API, a unit, an ownership rule, a concurrency guarantee, a format, error semantics.
- Spot: a call to a method or argument that you cannot find in the source or docs;
  a new `except Exception` or default that hides a case;
  a changed error or return value for a missing input.
- Fix: open the definition and confirm.
  If the repository cannot answer, state the uncertainty in the report, not in the code.

## Churn

- Failure: renames, reformatting, reordering,
  or rewrites of working code that the task did not ask for.
- Spot: hunks with no link to the stated goal,
  such as a reflowed signature or a renamed parameter.
- Fix: revert them.
  Report what you would change as a separate change.

## Tests as Proof

- Failure: a passing suite is taken as proof of correctness.
- Spot: a mock that accepts any call (`MagicMock`), so a nonexistent method passes;
  no test of the error path, the boundary, or the caller's expectation;
  a test that still passes when the change is reverted.
- Fix: test against a real or fake implementation, add the missing path,
  and check invariants and callers by reading.

## Imitating Bad Code

- Failure: a defect is copied because a neighbor has it.
- Spot: a suspicious pattern repeated from nearby code, such as swallowed errors.
- Fix: decide whether it is a convention, an accident, a workaround, or a bug.
  Verify before copying, and report a bug instead of spreading it.

## Comments as Understanding

- Failure: paragraphs of comment explain code that should be clearer.
- Spot: comments that narrate lines or restate a name, long comments on an ordinary function.
- Fix: improve names, structure, types, and control flow first.
  Keep a short comment only for a reason, constraint, or external fact that the code cannot show.
