# Smells

Read when auditing a codebase for smells or interpreting `scripts/change_coupling.py`. It covers
only the smells models miss or misjudge; the rest of Fowler's catalog (Long Function, Long Parameter
List, Duplicated Code, Feature Envy) is familiar and needs no card. For each, the report still gives
`file:line`, evidence, and a concrete change.

## Contents

- [Read the Repository's Rules First](#read-the-repositorys-rules-first)
- [Change Coupling](#change-coupling)
- [Divergent Change and Shotgun Surgery](#divergent-change-and-shotgun-surgery)
- [Hotspots](#hotspots)
- [Layout Smells](#layout-smells)
- [Speculative Generality](#speculative-generality)
- [Fowler Refactoring Names](#fowler-refactoring-names)
- [Report Entry](#report-entry)

## Read the Repository's Rules First

Linter configs, style guide, `AGENTS.md`, and framework conventions come before judging. A layout
the framework requires (Rails `app/models`, Django apps) is a constraint, not a smell. Exclude
generated, vendored, and third-party code and list the excluded paths.

## Change Coupling

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

## Layout Smells

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

## Speculative Generality

An interface, factory, option, or hook with one implementation or no caller. Confirm with `rg` for
callers and implementers, then inline it. Keep it when a published API or plugin contract needs it.

## Fowler Refactoring Names

Name the refactoring in the report's `Fix` line. Each links to its page in Fowler's catalog; the
language files show the idiom for each ([TypeScript](typescript.md), [Python](python.md),
[Rust](rust.md), [C](c.md), [C++](cpp.md), [C#](csharp.md), [Swift](swift.md),
[Kotlin](kotlin.md), [Scala](scala.md)).

| Smell | Refactoring |
| --- | --- |
| `if`/`else if` chain on one value | [Replace Conditional with Polymorphism](https://refactoring.com/catalog/replaceConditionalWithPolymorphism.html), or the language's exhaustive `switch`/`match` |
| Long or unclear condition | [Decompose Conditional](https://refactoring.com/catalog/decomposeConditional.html) |
| Branches with the same result | [Consolidate Conditional Expression](https://refactoring.com/catalog/consolidateConditionalExpression.html) |
| Nested conditions | [Replace Nested Conditional with Guard Clauses](https://refactoring.com/catalog/replaceNestedConditionalWithGuardClauses.html) |
| Boolean that selects behavior | [Remove Flag Argument](https://refactoring.com/catalog/removeFlagArgument.html) |
| Long parameter list | [Introduce Parameter Object](https://refactoring.com/catalog/introduceParameterObject.html) |
| String or number standing for a concept | [Replace Primitive with Object](https://refactoring.com/catalog/replacePrimitiveWithObject.html) |
| Repeated lines in every branch | [Slide Statements](https://refactoring.com/catalog/slideStatements.html), then hoist them |
| Unused code or shim | [Remove Dead Code](https://refactoring.com/catalog/removeDeadCode.html) |

Fowler's Remove Flag Argument example splits `setDimension(name, value)` into `setHeight` and
`setWidth`. The catalog pages are titles and links here; they were not re-read for this table, so
check the page before quoting a mechanic from it.

## Report Entry

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
