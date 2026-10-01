# Smells

Read when auditing a codebase for smells or interpreting `scripts/change_coupling.py`. It covers
only the smells models miss or misjudge; the rest of Fowler's catalog (Long Function, Long Parameter
List, Duplicated Code, Feature Envy) is familiar and needs no card. For each, the report still gives
`file:line`, evidence, and a concrete change.

## Contents

- [Read the repository's rules first](#read-the-repositorys-rules-first)
- [Change coupling](#change-coupling)
- [Divergent Change and Shotgun Surgery](#divergent-change-and-shotgun-surgery)
- [Hotspots](#hotspots)
- [Layout smells](#layout-smells)
- [Speculative generality](#speculative-generality)
- [Report entry](#report-entry)

## Read the repository's rules first

Linter configs, style guide, `AGENTS.md`, and framework conventions come before judging. A layout
the framework requires (Rails `app/models`, Django apps) is a constraint, not a smell. Exclude
generated, vendored, and third-party code and list the excluded paths.

## Change coupling

Two files are coupled when they change in the same commits, whether or not one imports the other.
The degree is the commits touching both divided by the average commits touching each (code-maat's
logical coupling).

```sh
python3 scripts/change_coupling.py --repo . --since 2025-01-01 --limit 10
```

Read the `cross` column first: high degree across directories means one feature is spread over
layers. Drop pairs that are expected to change together: a manifest and its lockfile, code and
`CHANGELOG`, a script and the docs that show its usage. Tests are excluded by default. Commits over
`--max-changeset` files (default 30) are skipped because bulk reformats and renames create false
pairs. With fewer than about 5 commits per file (code-maat's `--min-revs` default) say the history
is too short.

## Divergent Change and Shotgun Surgery

- Divergent Change: one file changes for unrelated reasons (history shows commits for different
  features touching it). Fix: split by reason to change.
- Shotgun Surgery: one logical change edits many small places (the same few files in many commits).
  Fix: move the scattered behavior into one module.

Both come from history, not from one snapshot; cite the commits or pairs.

## Hotspots

A file that is frequently changed and also long or complex costs most. Intersect
`git log --format= --name-only --since=DATE | sort | uniq -c | sort -rn | head` (POSIX; Git Bash on
Windows) with `scripts/file_length.py` output and the linter's complexity rule. A long file that
never changes is low priority.

## Layout smells

Report these with the directory or file pair as `Where`:

- Folders by kind (`components/`, `services/`, `models/`) when one feature spans them: group by
  feature if the framework allows.
- A name prefix standing in for a directory (`payment`, `payment-card`, `payment-card-validation`
  side by side).
- Numbered or leftover copies (`parser_old`, `report2`, `Copy of x`): delete after checking nothing
  imports them.
- Dumping grounds (`utils`, `helpers`, `common`, `misc`): move each function next to its caller.
- Stutter (`http/http_server.go`, `billing.BillingService`).

No catalog names the copies or prefix chains; write "no named smell" and describe them rather than
inventing a name.

## Speculative generality

An interface, factory, option, or hook with one implementation or no caller. Confirm with `rg` for
callers and implementers, then inline it. Keep it when a published API or plugin contract needs it.

## Report entry

```text
[smell] (source: Fowler 2018 | layout | no named smell)
Where:    path:line, or the file pair
Evidence: command and number printed, or the lines read
Cost:     what a reader or change pays today
Fix:      the concrete change
Keep if:  the condition that would make it not a smell
```

Order by cost: hotspots and cross-directory coupling first, cosmetic names last. Report only when
asked to report; do not fix during an audit.
