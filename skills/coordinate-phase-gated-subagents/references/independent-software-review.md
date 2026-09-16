# Review software independently for evidenced defects

Defect-focused review checks software requirements, design, or implementation
against evidence. Independent means a reviewer did not author the work and
evaluates it in a separate agent context. It does not authorize hostile
behavior, production probing, or manufacturing findings.

The reviewer is an independent fault-finder, not a second implementer and not a
style approver.

## Context

Give the reviewer:

- the diff or complete produced artifact;
- frozen requirements/design relevant to it;
- existing tests and execution evidence;
- interfaces/dependencies needed to reason about behavior.

Do not give the implementer's hidden reasoning merely to make the reviewer agree
with it. If design rationale is an official artifact, include that artifact.

## Reviewer instruction

Use an instruction equivalent to:

```text
Review this software change independently. Try to find concrete violations of
its recorded requirements or design, but report only findings supported by
source evidence or a reproducible counterexample. Do not presume that a defect
must exist. Trace edge cases, ownership,
lifetimes, concurrency, reentrancy, error paths, cleanup, platform behavior,
compatibility, and test blind spots. For each finding cite the exact location,
failure mechanism, affected requirement/design contract, and a reproduction or
proof strategy. Do not modify the implementation.
```

Choose the review scope for the evidenced risk. These are alternatives, not a
quota of three reviewers; do not launch all three by default:

- Reviewer A: semantic/API/edge-case correctness.
- Reviewer B: lifetime/concurrency/resource/error-path correctness.
- Reviewer C: portability/performance/security for high-risk units.

## Finding format

Use `assets/software-defect-review.template.md`. Findings need severity based on
impact, evidence, and contract violated—not rhetorical confidence.

## Disposition

The correction-and-integration agent classifies each finding:

- **accept** — defect is supported; fix and verify;
- **reject** — provide concrete counter-evidence;
- **upstream defect** — requirement/design is wrong or incomplete; open change
  control;
- **duplicate** — point to the original finding;
- **out of scope** — show why it is outside the frozen baseline.

A reviewer finding is not automatically correct. Independent review reduces
shared bias; it does not replace evidence.
