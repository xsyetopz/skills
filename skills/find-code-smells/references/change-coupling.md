# Change coupling

Smells that show in version history rather than in one snapshot of the
code: files that change together, files that change for too many reasons,
and changes that spread over many files. `scripts/change_coupling.py`
computes the pairs from `git log`; the cards say how to read them.

## Contents

- [Logical coupling](#logical-coupling)
- [Divergent Change](#divergent-change)
- [Shotgun Surgery](#shotgun-surgery)
- [Hotspots](#hotspots)
- [Run the coupling scan](#run-the-coupling-scan)

## Logical coupling

**Definition.** Two files are logically coupled when they tend to change
in the same commits, whether or not one imports the other. Gall, Hajek,
and Jazayeri introduced the idea from release history
([paper][gall]); Adam Tornhill's code-maat computes it: "Logical coupling
refers to modules that tend to change together" ([code-maat][code-maat]).
The degree of a pair is the number of commits that touch both, divided by
the average number of commits that touch each, as a percentage.

**Use when.**

- The layout scan or a review suggests one feature is spread across
  directories, and you need evidence from history.
- A change keeps breaking a file that nobody edited, and you want to know
  which files usually move with it.

**Do not use when.**

- The history is short: with fewer than about five commits per file
  (code-maat's `--min-revs` default is 5) the degrees are noise. Say that
  the history is too short.
- The pair is expected to change together: a manifest and its lockfile, a
  source file and its test (dropped by default), code and the
  `CHANGELOG`, a script and the documentation that shows its usage. List
  these as expected, not as smells.
- Most shared commits are bulk changes such as a reformat, a license
  header, or a rename. Commits over `--max-changeset` files (default 30)
  are skipped for that reason; lower it if bulk commits are smaller.

**Example.** Illustrative output for an order-handling service (the
summary line is wrapped):

```text
$ python3 scripts/change_coupling.py --since 2025-01-01 --limit 3
degree% shared avg-revs cross  pair
    82%     14       17   yes  src/api/orders.ts <-> src/db/order_rows.ts
    64%      9       14   yes  src/ui/OrderForm.tsx <-> src/api/orders.ts
    40%      6       15    no  src/api/orders.ts <-> src/api/pricing.ts
3 pairs reported (2 cross directories) of 3 above thresholds; 412 commits,
  380 files, 7 commits over 30 files skipped
```

The first two rows are one feature, orders, spread across `ui`, `api`,
and `db` directories ([folders by kind][by-kind]). Read the shared
commits before naming the smell:
`git log --oneline -- src/api/orders.ts src/db/order_rows.ts`.

**Cost removed.** Hidden dependencies: a change that must touch a file in
another directory, found only when something breaks.

**Verify.**

1. Each reported pair is marked expected or unexpected, with the reason.
1. For an unexpected pair, the report quotes two or more shared commit
   subjects that show the same change reaching both files.

## Divergent Change

**Definition.** One module changes for several unrelated reasons, so
each kind of change touches it. It is one of the smells in *Refactoring*
([catalog](smell-catalog.md)). refactoring.guru (a secondary source)
describes it as: "You find yourself having to change many unrelated
methods when you make changes to a class" ([refactoring.guru][divergent]).

**Use when.**

- A file has many commits, and their subjects fall into unrelated groups
  (for example, tax rules, PDF layout, and email delivery in one
  `invoice.py`).
- The file is logically coupled to several files that are not coupled to
  each other.

**Do not use when.**

- The commits are one concern evolving, even if many.
- The file is a composition root or a routing table whose job is to list
  every feature.

**Example.**

```sh
# Commit subjects that touched the file, to group by reason.
git log --format='%h %s' --since 2025-01-01 -- src/invoice.py
# The file's partners: rows where it appears with unrelated files.
python3 scripts/change_coupling.py --since 2025-01-01 --json |
  jq -r --arg f src/invoice.py '.pairs[]
    | select(.entity == $f or .coupled == $f)
    | "\(.degree)% \(.entity) \(.coupled)"'
```

Fix route: Split Phase or Extract Class along the groups of reasons
(`$write-readable-code`).

**Cost removed.** Merge conflicts between unrelated work, and a change for
one reason that breaks another.

**Verify.**

1. The report lists the groups of commit reasons with a count for each.
1. After a split, the next scan shows each new module coupled to one
   group of partners.

## Shotgun Surgery

**Definition.** One change needs many small edits in many modules, the
reverse of Divergent Change. refactoring.guru (a secondary source):
"Making any modifications requires that you make many small changes to
many different classes" ([refactoring.guru][shotgun]). It notes that it
can follow from "overzealous application of Divergent Change".

**Use when.**

- The coupling scan shows one file coupled to many others at a high
  degree, or a group of files that are all coupled to each other.
- Commits that implement one feature touch many directories with a few
  lines each: `git log --stat` shows it.

**Do not use when.**

- The edits are a planned migration or a rename across callers, done
  once.
- The spread comes from a layer-by-kind layout the framework requires;
  report it as the layout's cost ([folders by kind][by-kind]).

**Example.** Adding a field to an order edits `ui/OrderForm.tsx`,
`api/orders.ts`, `api/validation.ts`, `db/order_rows.ts`, and
`reports/orders.sql`. The scan shows `api/orders.ts` above 50% with each
of them. Fix route: Move Function and Move Field to gather the order
rules into one module, and Combine Functions into Class or a shared
schema that the others read (`$write-readable-code`, and
`$design-software-architecture` when the modules are separate packages).

**Cost removed.** Missed edits when one of the many places is forgotten.

**Verify.**

1. The report names the change and the files one instance of it touched
   (`git show --stat <commit>`).
1. The scan after the fix shows fewer partners for the central file.

## Hotspots

**Definition.** A hotspot is code that changes often and is hard to work
with, so effort goes into it again and again. CodeScene: "A Hotspot
analysis helps you identify those modules where you spend most of your
development time", and it "starts by identifying files with high change
frequency and low Code Health" ([CodeScene][codescene]). Change frequency
ranks where a smell costs most; a smell in a file nobody touches costs
little.

**Use when.**

- Ordering a smell report: put findings in hotspots first.
- Choosing which of many long or complex files to report.

**Do not use when.**

- The frequent changes are data or configuration edits (a translations
  file, a version constant), not code work.

**Example.**

```sh
# Commits per file since a date.
git log --since 2025-01-01 --format= --name-only | sed '/^$/d' |
  sort | uniq -c | sort -rn | head -20
# Code lines per file, from $write-readable-code's file_length.py.
python3 <write-readable-code>/scripts/file_length.py src --all --json
```

Join the two lists by path and report the files high on both, with both
numbers. Use complexity from the language's linter instead of length when
it is available ([tool thresholds](tool-thresholds.md)).

**Cost removed.** Time spent reporting smells in code that never changes.

**Verify.**

1. Each hotspot in the report shows its commit count, the date range, and
   its size or complexity with the tool that measured it.

## Run the coupling scan

```sh
python3 scripts/change_coupling.py --repo . --since 2025-01-01
python3 scripts/change_coupling.py --min-revs 10 --min-coupling 50 --json
python3 scripts/change_coupling.py --include-tests --limit 20
```

How it counts, following code-maat's `coupling` analysis:

- History: `git log --no-merges --no-renames --name-only`, one commit per
  change set. Merge commits are left out, and a renamed file counts as a
  new path.
- A commit with more than `--max-changeset` files (default 30) is
  skipped.
- Test files are dropped before counting unless `--include-tests` is
  given, because a test that changes with its code is expected.
- Degree = shared commits ÷ average of the two files' commit counts, as a
  whole percentage rounded down. A pair is reported when that average is
  at least `--min-revs` (5), the shared count is at least `--min-shared`
  (5), and the degree is at least `--min-coupling` (30). These are
  code-maat's defaults.
- `cross` is `yes` when the two files are in different directories.

Choose `--since` to cover the period the question is about; a start date
before a large restructure mixes two layouts. The summary line shows the
commits read, the files counted, and the commits skipped as too large;
put it in the report. Exit status 0 means no pair met the thresholds,
1 means pairs were reported, and 2 means no repository or bad options.

[gall]: https://plg.uwaterloo.ca/~migod/846/papers/gall-coupling.pdf
[code-maat]: https://github.com/adamtornhill/code-maat
[divergent]: https://refactoring.guru/smells/divergent-change
[shotgun]: https://refactoring.guru/smells/shotgun-surgery
[codescene]: https://codescene.io/docs/guides/technical/hotspots.html
[by-kind]: layout-smells.md#folders-by-kind-instead-of-by-feature
