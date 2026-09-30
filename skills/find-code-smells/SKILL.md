---
name: find-code-smells
description: >-
  Finds code smells with evidence from Fowler's catalog, folder layout, and
  change coupling in Git history. Use when asked to find or audit code smells
  or review structure. Not for security.
---

# Find Code Smells

A code smell is "a surface indication that usually corresponds to a
deeper problem in the system" ([Fowler][bliki]). Find the indications,
measure each one, name the smell from a published catalog, and route it
to the refactoring that removes it. This skill reports; fixing belongs
to `$write-readable-code` (functions, names, files) and
`$design-software-architecture` (packages and dependencies).

## Workflow

1. Write the scope: paths, revision, and what counts as generated or
   vendored code to leave out.
1. Read the repository's own rules first: linter configs, style guide,
   `AGENTS.md`, and framework conventions. A layout the framework
   requires (Rails `app/models`, Django apps) is not a smell.
1. Run the layout scan and keep its output:
   `python3 scripts/layout_smells.py src` (add `--max-files N` or
   `--max-depth N` only with a limit the team chose).
1. Run the change scan on the history:
   `python3 scripts/change_coupling.py --repo . --since <date>`
   ([method](references/change-coupling.md#run-the-coupling-scan)).
1. Run the language's own linter rules for size and complexity with their
   defaults ([thresholds](references/tool-thresholds.md)), or
   `$write-readable-code`'s `file_length.py` and
   `python_function_metrics.py`.
1. Read the code behind each lead. Name the smell from the
   [catalog](references/smell-catalog.md) or a layout card below, or
   state that no catalog names it.
1. Drop leads that a card's **Do not use when** covers, and say which
   condition dropped them.
1. Write the report in the format below, ordered by cost: hotspots and
   cross-directory coupling first, cosmetic names last.

## Route what you see to a card

| Seen in the tree or history | Card |
| --- | --- |
| `components/`, `services/`, `models/` at the top; one feature spans them | [Folders by kind][by-kind] |
| `payment`, `payment-card`, `payment-card-validation` side by side | [Prefix as directory][prefix] |
| `file1`/`file2`, `parser_old`, `report-final2`, `Copy of x` | [Numbered and leftover copies][copies] |
| `utils`, `helpers`, `common`, `misc`, repo-wide `types`, `constants` | [Dumping-ground and category files][dumping] |
| `http/http_server.go`, `billing.BillingService` | [Stutter][stutter] |
| A directory too long to scan, or paths many levels deep | [Crowded and deep directories][crowded] |
| Two files in different directories change together | [Change coupling][coupling] |
| One file changes for unrelated reasons | [Divergent Change][divergent] |
| One change edits many small places | [Shotgun Surgery][shotgun] |
| Frequently changed file that is also long or complex | [Hotspots][hotspots] |
| Long function, long parameter list, deep nesting, repeated switch | [Catalog: size and control flow][size] |
| Method uses another object's data more than its own | [Catalog: coupling smells][coupled] |
| Same code in several places | [Catalog: Duplicated Code][duplicated] |

## Report format

One entry per finding:

```text
[smell name] (source: Fowler 2018 | card name | no named smell)
Where:    path:line, or the directory, or the file pair
Evidence: tool, command, and the number it printed, or the lines read
Cost:     what a reader or a change pays today, concretely
Fix:      the refactoring and the card that applies it
Keep if:  the Do-not-use condition, when one applies
```

Group findings by smell. Put measured evidence apart from inference: a
count from a tool is measured, "this will be hard to change" is
inference, and the report says which is which.

## Rules

- Name a smell only from a catalog the report cites. When nothing in
  the catalogs fits (numbered copies, prefix chains), say "no named
  smell" and describe it; do not invent a name.
- A threshold is a tool's default or the team's choice, not a fact about
  quality. Quote the tool and the default when you use one.
- Report, do not fix. Edits start only when the user asks, and then
  through the fixing skill's cards and tests.
- Report a framework-mandated layout as a constraint, not a smell.
- Count what the report claims. "Many", "most", and "large" need the
  number behind them.
- Do not report a smell in generated, vendored, or third-party code; list
  the paths you excluded.
- Change coupling needs history: with fewer than about 5 revisions per
  file, code-maat's default minimum, say that the history is too short.

## Bundled tools

- `scripts/layout_smells.py PATH... [--min-group N] [--max-files N]
  [--max-depth N] [--exclude GLOB] [--include-tests] [--json]`: reports
  `prefix-group`, `numbered-sibling`, `generic-name`, `stutter`, and,
  when limits are given, `crowded-dir` and `deep-path`. Exit 0 clean, 1
  findings, 2 bad input.
- `scripts/change_coupling.py [--repo DIR] [--since DATE] [--min-revs N]
  [--min-shared N] [--min-coupling PCT] [--max-changeset N]
  [--include-tests] [--limit N] [--json]`: code-maat's logical coupling
  from `git log`, with a `cross` column for pairs in different
  directories. Exit 0 no pairs, 1 pairs, 2 bad input or no repository.

## Related skills

- `$write-readable-code`: apply the fix for function, name, and file
  smells; its `file_length.py` measures code lines per file.
- `$design-software-architecture`: package principles and dependency
  direction, for coupling that crosses modules.
- `$find-vulnerabilities`: security flaws, which are not smells.
- `$write-behavior-tests`: pin behavior before any refactoring starts.

## References

- [Smell catalog](references/smell-catalog.md): the 24 smells of
  *Refactoring* (2nd ed.), each with what to look for, a measurement, and
  the fix route, and when the code is not a smell.
- [Layout smells](references/layout-smells.md): folders by kind, prefix
  chains, numbered copies, dumping grounds, stutter, crowded and deep
  directories, with style-guide sources.
- [Change coupling](references/change-coupling.md): logical coupling,
  Divergent Change, Shotgun Surgery, hotspots, and how to run and read
  the scan.
- [Tool thresholds](references/tool-thresholds.md): default limits of
  ESLint, Pylint, Ruff, Clippy, golangci-lint, Checkstyle, PMD, detekt,
  SwiftLint, RuboCop, and duplicate detectors.

## Completion evidence

The report lists: the scope and the excluded paths; each command run and
its exit status; every finding in the format above; leads dropped and the
condition that dropped them; and the checks that could not run here, with
the reason.

[bliki]: https://martinfowler.com/bliki/CodeSmell.html
[by-kind]: references/layout-smells.md#folders-by-kind-instead-of-by-feature
[prefix]: references/layout-smells.md#name-prefix-standing-in-for-a-directory
[copies]: references/layout-smells.md#numbered-and-leftover-copies
[dumping]: references/layout-smells.md#dumping-ground-and-category-files
[stutter]: references/layout-smells.md#stutter
[crowded]: references/layout-smells.md#crowded-and-deep-directories
[coupling]: references/change-coupling.md#logical-coupling
[divergent]: references/change-coupling.md#divergent-change
[shotgun]: references/change-coupling.md#shotgun-surgery
[hotspots]: references/change-coupling.md#hotspots
[size]: references/smell-catalog.md#size-and-control-flow
[coupled]: references/smell-catalog.md#coupling-between-parts
[duplicated]: references/smell-catalog.md#duplicated-code
