# ARCHITECTURE.md

## Contents

- [Shape of the File](#shape-of-the-file)
- [Gather Evidence](#gather-evidence)
- [Durability](#durability)
- [Updating](#updating)
- [Placement](#placement)

## Shape of the File

Follow the codemap style of matklad's "ARCHITECTURE.md" post: a short file for someone who has never
seen the repository.

1. One paragraph on the problem the project solves and its overall approach.
1. A coarse code map. Per module or directory: what it is responsible for, the names of its entry
   points (files, types, functions), and what it deliberately does not do. Name the main types and
   call out the boundary layers.
1. Invariants, especially ones stated as an absence ("nothing under `core/` imports `http/`").
   Absences are invisible in code, so this is the part readers cannot rebuild by reading files.
1. Cross-cutting concerns that cut across modules (error handling, configuration, testing, security
   controls) when the code shows them.
1. Optionally a diagram. Its boxes must match the module names in the code map, with none added or
   missing.

Skip sections with no evidence. Do not write "Not evident" filler, template placeholders, or a
per-file listing; the reader has `ls`.

## Gather Evidence

- `git ls-files | cut -d/ -f1 | sort -u` (POSIX; Git Bash on Windows) for the top-level layout.
- Manifests and lockfiles, entry points, imports between packages, schemas and migrations, CI
  workflows, container and infrastructure files, authentication and validation code.
- Search the code for every technology, service, or control the document names
  (`rg -n -i 'redis|jwt'`). No match means it does not go in.
- Do not claim a security control unless code enforces it. A missing control is a fact to state.
- Express an invariant with a command that passes now and fails when the rule breaks, for example
  `! rg -q 'import http' core/`. Run it both ways.

## Durability

- Keep only facts that stay true through a refactor that preserves the architecture. Counts,
  versions, and per-function behavior go stale in weeks.
- Name files and symbols in backticks. Do not link local files and do not cite line numbers: links
  and line numbers break on the next edit, while names survive and symbol search finds them.
- Make the file self-contained. Agents often load only this file, so "see CONTRIBUTING.md" gives
  them nothing.
- Write history and rationale only when the repository records it. Label recommendations as
  recommendations.

## Updating

Audit drift first: run `scripts/check_architecture.py`, then re-check each module and invariant
claim against the code. Edit only the facts that changed and keep the structure the project chose. A
rewrite into another template throws away content the team wrote on purpose.

## Placement

The file is `ARCHITECTURE.md`, capitalized, at the repository root next to `README.md`. Move a
`docs/architecture.md` there with `mv` or `git mv`, update links to the old path, and keep one copy.
Commands for setup belong in the README, agent rules in AGENTS.md, and single decisions in ADRs.
