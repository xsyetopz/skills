---
name: write-readable-code
description: >-
  Restructures code so people and agents follow it without guessing and
  reviews it against the Zen of Python (PEP 20) in any language. Use when code
  is hard to follow or for a clarity, Pythonic, or Zen of Python review. Not
  for performance or PEP 8 formatting.
---

# Write Readable Code

Make the correct interpretation of code require as little inference as
possible. Each card has a runnable before/after example, a metric,
scanner, or type-checker signal, and the command that proves behavior did
not change. A Zen of Python (PEP 20) review uses the same cards through
the [aphorism map][zen-map], which links each of the 19 aphorisms to its
card.

## Workflow

1. Read the neighbors first: the file's existing ordering, naming, error
   style, test layout, language version, formatter and linter
   configuration, and public surface (`__all__`, exports, `pub`,
   published packages). The repository's conventions win over these
   templates.
1. Record baseline metrics for the functions you will touch:
   `uvx lizard -C 8 -L 40 -a 4 -ENS <files>` for most languages, and
   `python3 scripts/python_function_metrics.py <files>` for Python
   (lizard 1.24.0's nesting column is wrong for Python files). For a
   Zen of Python review of Python code, also run
   `python3 scripts/zen_scan.py <paths>`; for other languages, use the
   `rg` checks in the cards.
1. Pick cards from the routing table (or, for PEP 20 review, the
   [aphorism map][zen-map]) whose **Use when** matches what you see.
   Read each card's **Do not use when** before changing anything; many
   findings are correct as written.
1. Write or locate the check first: a test that pins current behavior
   (result, error type, and message), a mutant the test must reject, or
   a count that must drop.
1. Apply one card at a time, in the target language's idiom; run the
   test after each.
1. Place new declarations in the file order from
   [file layout](references/file-layout.md), with the narrowest
   visibility; widen only for an actual caller.
1. Review your diff with
   [agent failure modes](references/agent-failure-modes.md) and the cards
   its table links: no churn, synonyms, single-use abstractions, copied
   defects, or unverified facts, and a test that fails without the change.
1. Re-measure; report metric and scanner deltas and test results.

## Route what you see to a card

| Observation | Card |
| --- | --- |
| Happy path buried under nested `if`/`else` | [Guard clauses](references/function-shape.md#guard-clauses) |
| Validation, conversion, and computation interleaved | [Phases](references/function-shape.md#phases-validate-prepare-execute) |
| `a if x else b if y else c`, chained ternary, dense one-liner | [Lookup table](references/function-shape.md#lookup-table-instead-of-nested-conditional-expressions) |
| More than 4 parameters, same-typed positional args | [Parameter object](references/function-shape.md#parameter-object) |
| `if op == ...: elif op == ...:` chains | [Dispatch table](references/function-shape.md#dispatch-table-instead-of-an-ifelif-chain) |
| Compound boolean with 3+ concepts | [Explaining variables](references/function-shape.md#explaining-variables) |
| `f(x, True)` call sites | [Split flag arguments](references/function-shape.md#split-boolean-flag-arguments) |
| Tempted to extract a one-line helper | [When not to extract](references/function-shape.md#when-not-to-extract-a-function) |
| Need thresholds or a measurement command | [Function metrics](references/function-shape.md#function-metrics-and-limits) |
| Same concept under several names | [One concept, one term](references/names-and-types.md#one-concept-one-term) |
| `timeout`, `size`, `delay` without a unit | [Units](references/names-and-types.md#units-in-names-or-types) |
| Two IDs of the same primitive type in one signature | [Distinct ID types](references/names-and-types.md#distinct-identifier-types) |
| Several booleans describing one lifecycle | [Illegal states](references/names-and-types.md#illegal-states-unrepresentable) |
| Boolean function named `check`/`validate` | [Predicate names](references/names-and-types.md#predicate-names) |
| New code headed for `utils`/`helpers`/`common` | [Dumping grounds](references/names-and-types.md#no-dumping-ground-modules) |
| `data`, `tmp2`, `val` crossing functions | [Name length](references/names-and-types.md#name-length-follows-scope) |
| Name promises a different operation or unit | [Readability counts][readability] |
| Reads of globals, clock, env inside logic | [Explicit dependencies](references/state-errors-comments.md#explicit-dependencies-instead-of-ambient-state) |
| Computation and I/O in one function | [Pure core](references/state-errors-comments.md#pure-core-side-effects-at-the-edge) |
| `x or default`, `x \|\| default`, valid 0 or `""` replaced | [Explicit][explicit] |
| `except Exception`, `except: pass`, `_ =` on an error, wide `try` | [Specific errors](references/state-errors-comments.md#specific-error-handling-with-context) |
| Expected error ignored (file already gone, already exists) | [Explicitly silenced][silenced] |
| Unitless numbers, `03/04/2025`, conflicting keys, unverified API facts | [Refuse to guess][guess] |
| Comments narrating code | [Comments](references/state-errors-comments.md#comments-that-state-why) |
| Tests hiding inputs in helpers | [Tests as documentation](references/state-errors-comments.md#tests-as-executable-documentation) |
| Interface or factory with one implementation | [Simple][simple] |
| Retry, pagination, or locking copied at call sites | [Complex, not complicated][complex] |
| `if len == 0` before a loop that handles empty input | [Special cases][special] |
| "Impure" code with a measured reason | [Practicality][practical] |
| Two public entry points for one operation, or a second HTTP client | [One obvious way][one-way] |
| Public name being replaced | [Now][now] |
| New public helper or option without a caller | [Never right now][never] |
| Bit trick or clever code without a stated reason | [Hard to explain][explain] |
| `from x import *`, glob `use`, same name from two modules | [Namespaces][namespaces] |
| New file, or `public`/`pub`/`export` added | [File layout](references/file-layout.md#the-decision-order), then the language card |
| Reviewing an agent's diff, formatter noise | [Agent failure modes](references/agent-failure-modes.md) |
| Zen of Python, PEP 20, or "Pythonic" design review | [Aphorism map][zen-map] |

## Default limits

| Metric | Target | Review above |
| --- | --- | --- |
| Function NLOC | 30 | 40 |
| Cyclomatic complexity | 8 | 10 |
| Cognitive complexity | 10 | 15 |
| Nesting depth | 2 | 3 |
| Parameters | 4 | 6 |
| Local variables | 7 | 10 |
| Line width | 100 | 120 |

These are guardrails, not goals: a straight 45-line sequence can read
better than a 15-line function with nested branches, so do not split to
satisfy a count. The repository's linter limits win.

## Rules

- Behavior first: every restructuring keeps results, error types, error
  messages, ordering of checks, and side effects. Prove it with a test
  that compares outcomes before and after, run before the old code is
  deleted.
- One concept, one term; different concepts, different terms. Reuse the
  repository's vocabulary.
- No new helper, interface, framework, or dependency without a present
  need; say what it is for in the report.
- Do not guess units, ownership, concurrency, platform behavior, formats,
  or error semantics. Verify from the source, or mark it unverified and
  report it.
- Keep diffs narrow: no renames, reformatting, or reordering of untouched
  code. Do not add a formatter or change linter configuration as part of
  a design fix; leave PEP 8 layout to the project's formatter.
- Do not rename published names, wire fields, or generated code. Report
  them, or deprecate them with a warning.
- Silence only a named error type around one operation, and give the
  reason next to it.
- Present PEP 20 readings as this skill's interpretation, never as the
  PEP's text, and never claim a codebase "complies with PEP 20". Report a
  finding as a defect only with evidence: a failing mutant, a count, a
  measurement, or a reproduced bug.
- Comments state why or an external fact; never what the next line does.
- A green test suite proves only what it exercises: name the test that
  covers each changed behavior.

## Bundled tools

- `scripts/python_function_metrics.py PATH... [--max-nloc N] [--max-ccn N]
  [--max-nesting N] [--max-params N] [--json]`: per-function metrics for
  Python; exit 1 when a limit is exceeded.
- `scripts/term_report.py PATH... --group concept=canonical,alt,...`:
  counts competing terms across identifiers; exit 1 on drift.
- `scripts/zen_scan.py PATH... [--json]`: AST scanner for
  `silenced-except`, `broad-except`, `wide-suppress`, `or-default`, and
  `star-import`; exit 0 clean, 1 with findings, 2 on unreadable input.
- `sh assets/examples/readable/verify.sh examples|types|layout|all`: runs
  the before/after oracles and metric deltas, the typed-ID misuse checks
  (rustc, tsc, pyright), and compiles or runs every layout template.
- `sh assets/examples/zen-of-python/verify.sh [measure]`: runs the Zen of
  Python examples (Python, TypeScript, Go, Rust, Java, C) with mutants and
  scanner counts; a missing toolchain prints `SKIP` with its card.
- `assets/layout/<language>/template.*`: file skeletons for Python, Rust,
  Go, C, C++, C#, F#, Java, Kotlin, Scala, JavaScript, TypeScript, Swift,
  Ruby, and Lua.

## References

- [Function shape](references/function-shape.md): read when restructuring
  a function; metrics and limits, guard clauses, phases, lookup and
  dispatch tables, parameter objects, explaining variables, flag
  arguments, when not to extract.
- [Names and types](references/names-and-types.md): read when naming or
  typing values; canonical terms, units, typed IDs, enums over flag sets,
  predicates, module names, name length.
- [State, errors, comments, and tests](references/state-errors-comments.md):
  read for hidden inputs, I/O mixed with logic, error handling, comments,
  and tests.
- [Zen of Python](references/zen-of-python.md): read for a PEP 20 or
  Pythonic review; the aphorism map plus explicit defaults, silencing,
  guessing, abstraction, public surface, explainability, and namespaces.
- [File layout and visibility](references/file-layout.md): read when
  adding a file or widening visibility; decision order and one card per
  language with its graph and template.
- [Agent failure modes](references/agent-failure-modes.md): read before
  reporting a diff; churn and formatting, tests as proof, copied defects,
  and the review order.

## Completion evidence

The report contains: the cards applied and why (for a PEP 20 review, the
aphorism, `file:line`, and the evidence: scanner output, a reproduction,
or a count); before/after metrics, scanner, or symbol counts for each
touched function; the behavior test command and result, and that it fails
when the change is reverted; the terminology report if names changed;
findings left unchanged with the **Do not use when** condition that kept
them; the `git diff --stat`; facts left unverified; and checks not
runnable here, with the reason.

## Stop and ask

- The fix changes a published API, a wire format, or stored data.
- Two readings of an ambiguous input are both in use by real callers.
- A practicality exception needs a measurement the environment cannot
  produce.

[zen-map]: references/zen-of-python.md#aphorism-map
[readability]: references/zen-of-python.md#readability-counts
[explicit]: references/zen-of-python.md#explicit-is-better-than-implicit
[silenced]: references/zen-of-python.md#unless-explicitly-silenced
[guess]: references/zen-of-python.md#refuse-the-temptation-to-guess
[simple]: references/zen-of-python.md#simple-is-better-than-complex
[complex]: references/zen-of-python.md#complex-is-better-than-complicated
[special]: references/zen-of-python.md#special-cases-arent-special-enough-to-break-the-rules
[practical]: references/zen-of-python.md#although-practicality-beats-purity
[one-way]: references/zen-of-python.md#there-should-be-one-obvious-way-to-do-it
[now]: references/zen-of-python.md#now-is-better-than-never
[never]: references/zen-of-python.md#although-never-is-often-better-than-right-now
[explain]: references/zen-of-python.md#if-the-implementation-is-hard-to-explain
[namespaces]: references/zen-of-python.md#namespaces-are-one-honking-great-idea
