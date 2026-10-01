# Readability

Read when restructuring a function, naming or typing values, or handling errors and comments. Every
change needs a pinned-behavior test first, and the repository's conventions win over these.

## Contents

- [Function shape](#function-shape)
- [Names and types](#names-and-types)
- [State and errors](#state-and-errors)
- [Comments](#comments)
- [Files](#files)
- [Reviewing your own diff](#reviewing-your-own-diff)

## Function shape

- Happy path buried in nested `if`/`else`: use guard clauses with early returns, keeping the order
  of checks so the first error raised is the same one.
- Validation, conversion, and computation interleaved: separate them into phases only when each
  phase is named by what it guarantees.
- Nested or chained conditional expressions: replace with an early return plus a lookup table,
  compute shared values (such as a cap) once.
- `if op == ...: elif ...:` chains over one value: a dispatch table, unless branches differ in
  shape.
- More than 6 parameters (the default limit below) or same-typed positional arguments: a parameter
  object.
- `f(x, True)` call sites: split the function or use a named option.
- A compound boolean with 3 or more concepts: explaining variables.
- Do not extract a one-line helper used once; the call site already reads fine and the reader now
  jumps.
- Default review limits, used only when the repository has none: NLOC 40, cyclomatic complexity 10,
  nesting 3, parameters 6, line width 120. They are guardrails, not goals.

## Names and types

- One concept, one term; different concepts, different terms. Count competing terms with `rg -c`
  before picking the canonical one.
- Units belong in the name or the type (`timeout_ms`, `Duration`).
- Two IDs of the same primitive type in one signature: distinct ID types.
- Several booleans describing one lifecycle: an enum, so illegal states cannot be represented.
- A boolean function named `check` or `validate`: name it as a predicate (`is_valid`, `has_access`).
- Name length follows scope; `data`, `tmp2`, `val` should not cross functions.
- Do not rename published names, wire fields, or generated code.

## State and errors

- Reads of globals, the clock, or the environment inside logic: pass them in.
- Computation and I/O in one function: a pure core with I/O at the edge, when a test needs one of
  them alone.
- `x or default` / `x || default` replaces valid `0` and `""`: test for `None` or `undefined`
  explicitly.
- `except Exception`, bare `except`, ignored error results, and wide `try` blocks: catch the named
  type around one operation and add context.
- An expected error (file already gone) may be silenced by type, with the reason beside it.

## Comments

State why, or an external fact (a spec section, a bug id). Delete comments that narrate the next
line or restate a name. Tests are documentation: keep inputs and expected values visible in the
test, not hidden in helpers.

## Files

Split a file only by responsibility, never by count alone. A default of 300 code lines per source
file and 500 per test file is a review trigger, not a rule; run `scripts/file_length.py`. New
declarations go in the file's existing order, with the narrowest visibility; widen only for an
actual caller.

## Reviewing your own diff

- Unrelated renames, reformatting, or reordering: revert them.
- A new name for a concept that already has one: use the existing term.
- A helper, interface, or dependency with one use: inline it.
- A copied defect: a pattern copied from nearby code that is wrong there too; report it, do not
  spread it.
- A fact you did not verify (unit, format, API behavior): mark it.
- The behavior test fails when the change is reverted.
