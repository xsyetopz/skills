---
name: refactor-code-smells
description: >-
  Refactors code smells: if/else-if chains comparing one value with == or ===, flag arguments, deep
  nesting, duplicated branches, long parameter lists, stringly-typed state, primitive obsession, and
  dead shims, fallbacks, or legacy paths. Use when cleaning up, simplifying, or reviewing working
  code without changing behavior. Not for $apply-architecture-patterns or speed.
when_to_use: >-
  This function is five levels of nested ifs. Replace this if/else chain with a match. Drop the
  tomli fallback now that we need 3.11. Find the smells in orders.py, report only. Delete the
  feature flag that has been on for two releases.
---

# Refactor Code Smells

Cleanup changes working code, so the risk is silent behavior change and deleted paths that something
still uses. Agents write the same smells they are asked to remove, skip the safety steps, and
over-edit; these rules counter that.

## Rules

- Pin behavior before refactoring. Write or locate a test that fails if the result, error type,
  error message, or side effect changes, and run it before and after each step; a green suite only
  proves what it exercises.
- Keep refactor and behavior change in separate diffs. Report a bug you find while refactoring
  instead of fixing it inside the refactor, so the diff can be reviewed as "no behavior change".
- Do not write the smells this skill removes. In new and touched code:
  - An `if`/`else if` chain comparing one value with `==` or `===` becomes the language's `switch`
    or `match` with its exhaustiveness check on, or a lookup table when every branch only maps a
    key to a value. A table loses the exhaustiveness check, so prefer `match` over a closed set.
  - A boolean that selects behavior (`render(true)`) becomes two functions or an enum, unless the
    language labels the argument at the call site (Swift labels, named arguments).
  - Nested conditions become guard clauses with early returns, keeping the order of checks so the
    first error raised stays the same.
  - Branches that repeat the same lines get the shared lines moved out of the branch.
  - A string or bare number with a closed set of values or a unit becomes an enum or a newtype.
  - More than about 4 positional parameters, or several of one type, become a parameter object.
- Follow a repository convention unless it is a smell this skill names. Then use the better form in
  touched code, name the convention with evidence (`file:line`, how often it appears, and its
  maintenance cost), and ask before migrating untouched code.
- Stay inside the requested scope. No renames, reformatting, reordering, or linter or formatter
  changes on untouched code, and no renaming of public names, wire fields, or generated code; report
  them instead. Noise hides the real change from review.
- Add no abstraction for one caller: no interface with one implementation, no factory, no helper
  extracted from a single use, no `utils` module. Extract only when it removes real duplication or
  names a concept; the indirection is a cost the reader pays.
- Do not delete compatibility code without evidence. Age, a failing test, or an empty local search
  is not evidence. Check the support policy (minimum versions), every caller (code, strings, config,
  registries), stored or persisted data, public API and exports, docs, and external clients. Stored
  data outlives code: keep readers of old formats until a migration retires them. Details in
  [compatibility removal](references/compatibility-removal.md).
- Remove completely once removal is proven: the old path, its dedicated tests, dependencies,
  exports, docs, and flags. A forwarding wrapper or fallback left "just in case" is the same dead
  code under a new name. Delete superseded internal code in the change that adds the new path.
- Stop and ask the user before removing a supported public API; it needs a major version and
  changelog entry that the user schedules.
- Comments state why or an external fact, never what the next line does. Delete comments that
  restate code; rename instead when the code needs explaining.
- Report every smell with `file:line`, the evidence (a tool count or the lines read), and the
  concrete change that fixes it. "This file is messy" is not a finding. A number a tool printed is
  measured; "hard to change" is inference, and the report says which is which.
- Do not name a smell the repository requires (a framework-mandated layout, generated or vendored
  code). Tool thresholds are defaults or team choices, so quote the tool and its default.
- Do not split a function only to satisfy a metric. A straight 45-line sequence can read better than
  a 15-line function with nested branches; the repository's linter limits win.
- Do not guess units, formats, ownership, or error semantics while clarifying names or types. Verify
  from the source or mark it unverified.
- Silence only a named error type around one operation, with the reason beside it; never
  `except Exception: pass` or an ignored error result.
- Report-only requests stay report-only: do not edit until asked.

## Workflow

1. Read the neighbors first: the file's ordering, naming, error style, test layout, language
   version, formatter and linter config. The language version decides which forms exist (Python
   `match` needs 3.10).
1. Find leads: the language's linter with its defaults, `python3 scripts/file_length.py` for long
   files, and `python3 scripts/change_coupling.py` for files that change together. Read the code
   behind each lead before naming a smell.
1. Pin behavior with a test. For removals, trace consumers first ([compatibility
   removal](references/compatibility-removal.md)).
1. Apply one change at a time and run the test after each. Turn on the compiler or linter check
   that guards the new form (exhaustive `switch`, unused code) if the repository already enables
   it for other files.
1. Review your own diff: no churn, no synonyms for existing terms, no single-use abstractions, no
   copied defects, and a test that fails if the change is reverted.
1. Report: what changed, the test command and its result, each check you skipped by name, what you
   left alone and why, and facts you could not verify.

## Scripts

- `python3 scripts/change_coupling.py [--repo DIR] [--since DATE] [--min-revs N] [--min-shared N]
  [--min-coupling PCT] [--max-changeset N] [--include-tests] [--limit N] [--json]` lists file pairs
  that change in the same commits, with a `cross` column for pairs in different directories. One
  pair per line. Exit 0 no pairs, 1 pairs, 2 usage error or no repository. With fewer than about 5
  revisions per file the history is too short to mean anything.
- `python3 scripts/file_length.py PATH... [--max-code N] [--max-test N] [--test-glob GLOB]
  [--exclude GLOB] [--all] [--json]` counts code lines (no blanks, comments, or docstrings) per file
  for about 25 language families, tests separate. One file per line. Exit 0 clean, 1 a file over its
  limit (defaults 300 source, 500 test), 2 usage error. `line_count.py` is its counting module.
- Tests: `python3 -m unittest discover -s scripts`. On Windows, use `py -3` for `python3`.

## References

- Read [`references/smells.md`](references/smells.md) when reviewing or auditing a codebase for
  smells, or when interpreting `change_coupling.py` output.
- Read [`references/readability.md`](references/readability.md) when restructuring a function,
  naming values, or handling errors and comments.
- Read [`references/compatibility-removal.md`](references/compatibility-removal.md) before deleting
  any fallback, alias, version branch, flag, or legacy reader.
- Read the file for the language you are editing before replacing a branch chain, a flag argument,
  or a primitive: [TypeScript and JavaScript](references/typescript.md),
  [Python](references/python.md), [Rust](references/rust.md), [C](references/c.md),
  [C++](references/cpp.md), [C#](references/csharp.md), [Swift](references/swift.md),
  [Kotlin](references/kotlin.md), [Scala](references/scala.md).
