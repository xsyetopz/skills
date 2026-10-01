---
name: improve-code-quality
description: >-
  Finds code smells and refactors for readability, and removes dead
  compatibility shims, fallbacks, and legacy paths. Use for cleanup or review
  of working code. Not for performance.
---

# Improve Code Quality

Cleanup changes working code, so the risk is silent behavior change and deleted paths that something
still uses. Models skip the safety steps and over-edit; these rules counter that.

## Rules

- Pin behavior before refactoring. Write or locate a test that fails if the result, error type,
  error message, or side effect changes, and run it before and after each step; a green suite only
  proves what it exercises.
- Keep refactor and behavior change in separate diffs. Report a bug you find while refactoring
  instead of fixing it inside the refactor, so the diff can be reviewed as "no behavior change".
- Stay inside the requested scope. No renames, reformatting, reordering, or linter/formatter changes
  on untouched code, and no renaming of public names, wire fields, or generated code; report them
  instead. Noise hides the real change from review.
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
  code under a new name.
- Delete superseded internal code in the same change that introduces the new path; for a public API
  follow the next rule.
- Stop and ask the user before removing a supported public API; it needs a major version and
  changelog entry that the user schedules.
- Comments state why or an external fact, never what the next line does. Delete comments that
  restate code; rename instead when the code needs explaining.
- Report every smell with `file:line`, the evidence (a tool count or the lines read), and the
  concrete change that fixes it. "This file is messy" is not a finding. A number a tool printed is
  measured; "hard to change" is inference, and the report says which is which.
- Name a smell only when it is one: drop a finding the repository requires (a framework-mandated
  layout, generated or vendored code, a repo convention). Tool thresholds are defaults or team
  choices, not facts about quality, so quote the tool and default.
- Do not split a function only to satisfy a metric. A straight 45-line sequence can read better than
  a 15-line function with nested branches; the repository's linter limits win.
- Do not guess units, formats, ownership, or error semantics while clarifying names or types. Verify
  from the source or mark it unverified.
- Silence only a named error type around one operation, with the reason beside it; never
  `except Exception: pass` or an ignored error result.
- Report-only requests stay report-only: do not edit until asked.

## Workflow

1. Read the neighbors first: the file's ordering, naming, error style, test layout, language
   version, formatter and linter config. The repository's conventions win over this skill.
1. Find leads: the language's linter with its defaults, `python3 scripts/file_length.py` for long
   files, and `python3 scripts/change_coupling.py` for files that change together. Read the code
   behind each lead before naming a smell.
1. Pin behavior with a test. For removals, trace consumers first ([compatibility
   removal](references/compatibility-removal.md)).
1. Apply one change at a time and run the test after each.
1. Review your own diff: no churn, no synonyms for existing terms, no single-use abstractions, no
   copied defects, and a test that fails if the change is reverted.
1. Report: what changed, the test command and result, what you left alone and why, and facts you
   could not verify.

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
