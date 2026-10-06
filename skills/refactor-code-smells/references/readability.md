# Readability

Read when restructuring a function, naming or typing values, or handling errors and comments.
Every change needs a pinned-behavior test first,
and the repository's conventions win over these.

Write ordinary code so a beginner can follow its control flow,
an intermediate reader can change it without rebuilding the subsystem,
and an advanced reader can see the design.
Optimize for low ambiguity and low working-memory cost,
not for fewer lines or fewer files.
For a diff written by an agent,
also read [agent failure modes](agent-failure-modes.md).

## Contents

- [Function Shape](#function-shape)
- [Review Limits](#review-limits)
- [Names and Types](#names-and-types)
- [State and Errors](#state-and-errors)
- [Comments](#comments)
- [Files and Locality](#files-and-locality)
- [Tests and Formatting](#tests-and-formatting)
- [Reviewing Your Own Diff](#reviewing-your-own-diff)
- [Review Order](#review-order)

## Function Shape

- Happy path buried in nested `if`/`else`: use guard clauses with early returns,
  keeping the order of checks so the first error raised is the same one.
- Validation, conversion, and computation interleaved:
  separate them into phases only when each phase is named by what it guarantees.
- Nested or chained conditional expressions:
  replace with an early return plus a lookup table,
  compute shared values (such as a cap) once.
- `if op == ...: elif ...:` chains over one value:
  a dispatch table, unless branches differ in shape.
- More than 6 parameters (the review limit below) or same-typed positional arguments:
  a parameter object.
- `f(x, True)` call sites: split the function or use a named option.
- A compound boolean with 3 or more concepts: explaining variables.
- Do not extract a one-line helper used once;
  the call site already reads fine and the reader now jumps.
- Extract a block when it has its own purpose, abstraction level, or invariant,
  and a name says it better than a comment would.
- Hidden control flow costs the reader:
  callback pyramids, operators with side effects,
  reflection for ordinary dispatch, and macros that change the apparent flow.
  Prefer early exits and visible phases (validate, prepare, execute, handle the result),
  separated by blank lines.

## Review Limits

Use these only when the repository has no limits of its own.
They are guardrails, not goals.
Aim for the target;
a function over the review value needs a reason or a change.

| Metric | Target | Review |
| --- | ---: | ---: |
| Function body (NLOC) | 30 or fewer | over 40 |
| Cognitive complexity | 10 or fewer | over 15 |
| Cyclomatic complexity | 8 or fewer | over 10 |
| Nesting depth | 2 or fewer | over 3 |
| Parameters | 4 or fewer | over 6 |
| Local variables | 7 or fewer | over 10 |
| Line width | 100 or fewer | over 120 |

## Names and Types

- One concept, one term; different concepts, different terms.
  Count competing terms with `rg -c` before picking the canonical one.
- Units belong in the name or the type (`timeout_ms`, `Duration`).
- Two IDs of the same primitive type in one signature: distinct ID types.
- Several booleans describing one lifecycle:
  an enum, so illegal states cannot be represented.
- A boolean function named `check` or `validate`:
  name it as a predicate (`is_valid`, `has_access`).
- Name length follows scope; `data`, `tmp2`, `val` should not cross functions.
- A name should save the reader a lookup:
  `remaining_bytes` and `candidate_paths`, not `rem` or `thing`.
  A function name says what it does (`parse_config`, `load_user`).
- Do not rename published names, wire fields, or generated code.

## State and Errors

- Reads of globals, the clock, or the environment inside logic: pass them in.
- Service locators, thread-local state, and singleton mutation hide the data flow;
  show what enters and leaves a function.
- Computation and I/O in one function:
  a pure core with I/O at the edge, when a test needs one of them alone.
- `x or default` / `x || default` replaces valid `0` and `""`:
  test for `None` or `undefined` explicitly.
- `except Exception`, bare `except`, ignored error results, and wide `try` blocks:
  catch the named type around one operation and add context.
- An expected error (file already gone) may be silenced by type, with the reason beside it.
- A reader should see what may fail, where context is added, and where recovery happens.
  Do not turn a specific error into a generic one,
  log and ignore without a reason,
  or log the same failure at every layer.

## Comments

State why, or an external fact (a spec section, a bug id).
Delete comments that narrate the next line or restate a name.
Keep a comment next to the code it constrains.
A function that needs paragraphs of comment is too hard to read;
fix names, structure, and types first.

## Files and Locality

Split a file only by responsibility, never by count alone.
A default of 300 code lines per source file and 500 per test file is a review trigger,
not a rule; run `scripts/file_length.py`.
New declarations go in the file's existing order, with the narrowest visibility;
widen only for an actual caller.
Do not add a file whose only theme is "did not fit elsewhere" (`utils`, `misc`, `common`).

Keep code that is understood together close:
a validation and the operation it protects,
an invariant and its enforcement,
a type and its main behavior,
error translation and the boundary that needs it.
Each jump to another file costs a human attention and an agent a context fetch.

## Tests and Formatting

A test shows setup, action, expected result, and the boundary it covers,
under a name that states the behavior.
Keep inputs and expected values visible in the test, not hidden in helpers;
a helper that hides the behavior under test makes the reader debug the harness.

Leave formatting to the repository's formatter, import sorter, and lint rules.
Do not align code by hand;
prefer layouts that stay stable when one argument or case is added.

## Reviewing Your Own Diff

- Unrelated renames, reformatting, or reordering: revert them.
- A new name for a concept that already has one: use the existing term.
- A helper, interface, or dependency with one use: inline it.
- A copied defect: a pattern copied from nearby code that is wrong there too;
  report it, do not spread it.
- A fact you did not verify (unit, format, API behavior): mark it.
- The behavior test fails when the change is reverted.

## Review Order

Check in this order, and report at the first failure before commenting on later items:

1. Behavior is correct and invariants hold.
1. The architecture is still coherent and the control flow is obvious.
1. Names and terms match the repository, and state and side effects are explicit.
1. The abstraction level is consistent and the working-memory load is reasonable.
1. The diff is no wider than it must be.
1. Style details last.
   Well-formatted code that confuses is not approved.
