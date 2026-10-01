# Requirements

Read when writing requirement statements, behavior models, or acceptance criteria. Follow the
repository's own spec format when it has one (for example a `docs/specs/README.md`); the forms below
fill the gaps.

## Line format

`REQ-<AREA>-<NNN> [source: <where it came from>] <EARS statement>`, with one `shall`. Acceptance:
`AC-<AREA>-<NNN> verifies REQ-<AREA>-<NNN>: Given ..., when ..., then ...`. Open question:
`DEC-<AREA>-<NNN>: <question>`.

A source is the request, an issue, a design review, or a standard section
(`[source: RFC 9110 section 9.3.5]`). "Best practice" is never a source.

## EARS patterns

EARS (Easy Approach to Requirements Syntax, Mavin et al., RE 2009) has six forms; pick the one that
matches the trigger.

- Ubiquitous: `The <system> shall <response>.`
- Event-driven: `When <trigger>, the <system> shall <response>.`
- State-driven: `While <state>, the <system> shall <response>.`
- Unwanted behavior: `If <condition>, then the <system> shall <response>.`
- Optional feature: `Where <feature is included>, the <system> shall ...`
- Complex: `While <state>, when <trigger>, the <system> shall ...`

Error handling, misuse, and failures use the unwanted-behavior form; a spec with only happy-path
statements is unfinished.

## One response per requirement

A statement with "and" between two responses is two requirements, because one acceptance test cannot
fail for exactly one reason. Split it.

## Normative keywords

MUST, SHOULD, and MAY carry their meaning only in capitals (RFC 2119, RFC 8174). If the repository
writes `shall`, do not mix in `should`.

## Measurable quality and vague terms

"Fast", "scalable", "reliable", "robust", and "appropriate" have no pass or fail. Replace each with
a scenario: stimulus, environment, response, measure (`p95 latency under N requests per second`), or
with a `DEC-` item when nobody has given the number. Do not fill in the number yourself.

```text
Bad:  REQ-UP-001 Uploads shall resume within 5 seconds.
Good: DEC-UP-001: How soon after a dropped connection must an upload resume,
      and what is the maximum gap that still counts as the same upload?
```

## Behavior models

Use a model only when prose would leave a gap.

- Glossary: for each noun, its identity and lifetime (is a "session" the login, the tab, or the
  token?). Fix units and domains (milliseconds or seconds, inclusive or exclusive bounds, UTC or
  local).
- State transition table for anything with a lifecycle: state, event, next state, and the cells that
  are forbidden. Empty cells are unspecified behavior; fill each or add a `DEC-`.
- Decision table when three or more conditions interact: one row per combination, one outcome each.
  Missing combinations are findings.
- Races: name the linearization point (the one atomic operation that decides which request wins).
  Without it, "two users book the last seat" has no defined outcome.
- Retries and duplicates: state whether repeating a request is the same operation (same key, same
  result) or a new one.
- Abuse cases at trust boundaries: who may call, what an unauthorized caller sees, what a replayed
  or oversized input does.

## Acceptance criteria

- Observe at the contract boundary: a response, return value, stored row, emitted event, or file.
  Not private fields, call counts, or class names.
- Include boundaries: the limit, one below, one above; empty; the first and last state; the failure
  path for each `If/then` requirement.
- Every requirement has at least one criterion, and every criterion names an existing requirement.
- Test races with a barrier or an explicit interleaving; a `sleep` makes the test flaky and proves
  nothing.

## Criterion to test

Name each test after its criterion ID, one test per criterion. After the test passes, break the
behavior (flip the comparison, drop the check) and confirm the test fails; a test that stays green
proves nothing. Do this only when code exists.

## Do not

- Put implementation (table names, classes, libraries) in a requirement unless the request
  constrains it.
- Write requirements from the current code as if they were intent; a bug in the code is not a
  requirement.
