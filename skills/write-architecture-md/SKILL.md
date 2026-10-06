---
name: write-architecture-md
description: >-
  Writes and audits ARCHITECTURE.md as a codemap of modules,
  entry points, boundaries, and invariants checked against the code.
  Use when creating an ARCHITECTURE.md, explaining how modules fit together,
  or fixing one that names code that no longer exists.
  Not for READMEs, AGENTS.md, or redesigns.
---

# Write ARCHITECTURE.md

Give a reader who has never seen the repository a map of the code: what each module does, where it
starts, what it must not do, and the rules that hold across modules. Every statement matches the
code as it is today.

## Rules

- ARCHITECTURE.md names modules, their boundaries, invariants, and entry points (a codemap). It is
  not a file-by-file listing, a tour of dependencies, or a template with every section filled.
  Anything the code does not show is left out.
- Search the code for every technology, service, and security control before naming it. When the
  user asks to document something the code does not have, such as a cloud setup or an auth flow, say
  so instead of writing it.
- Describe what the code does now. Leave out plans and roadmaps, and label recommendations as
  recommendations.
- When the document and the code disagree, fix the document unless the user asked for a code change.
  Report the disagreement if it is unclear which is wrong.
- Name files and symbols in backticks. Do not link local files or cite line numbers; both break on
  the next edit.
- Write an invariant with a command that passes now and fails when the rule breaks, and run it.
- The file is `ARCHITECTURE.md` at the repository root. Move a `docs/architecture.md` there and
  update links to it.
- Write headings in the title case of the document's language, as `$format-github-markdown`
  describes ("Data Flow and Invariants" in English).
- Leave READMEs and setup docs to `$write-project-readme`, Markdown syntax and line wrapping to
  `$format-github-markdown`, and agent rules to AGENTS.md.

## Workflow

1. Read the layout, manifests, entry points, imports between packages, and CI.
1. For an existing file, run `scripts/check_architecture.py` and re-check each claim against the
   code. Edit only the facts that changed and keep the structure the project chose.
1. Write or update the file: purpose, code map, invariants, cross-cutting concerns.
1. Run the checker and each invariant command, fix the findings, and rerun.
1. In the reply, list what was run and every requested topic left out because the code does not show
   it.

## Scripts

Run these from the skill directory or by full path. On Windows, use `py -3` for `python3`.

- `python3 scripts/check_architecture.py ARCHITECTURE.md [--json | --commands]` checks the file name
  and placement, empty sections, placeholders, tree and backticked paths that do not exist,
  undescribed top-level directories, and warns on local links and `file:line` references.
  `--commands` lists the commands to run. Exit 0 no errors, 1 errors, 2 bad input. It cannot detect
  invented technology; search the code for each one instead.
- Tests: `python3 -m unittest discover -s scripts`.

## References

- Read [ARCHITECTURE.md](references/architecture.md) when creating, updating, or auditing an
  ARCHITECTURE.md.
