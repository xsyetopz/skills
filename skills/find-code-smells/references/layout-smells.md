# Layout smells

Smells in how files and directories are named and grouped. Most of them
have no name in Fowler's catalog. Where a style guide or linter names the
problem, the card cites it. Where nothing names it, the card says so, and
a report should say "no named smell" rather than invent one.

`scripts/layout_smells.py` finds the leads for the first five cards; the
last card needs limits the team chose. Its finding kinds are
`prefix-group`, `numbered-sibling`, `generic-name`, `stutter`,
`crowded-dir`, and `deep-path`. It lists directories with
`git ls-files` when it can, and skips test files unless
`--include-tests` is given.

## Contents

- [Folders by kind instead of by feature][toc-1]
- [Name prefix standing in for a directory][toc-2]
- [Numbered and leftover copies](#numbered-and-leftover-copies)
- [Dumping-ground and category files](#dumping-ground-and-category-files)
- [Stutter](#stutter)
- [Crowded and deep directories](#crowded-and-deep-directories)

[toc-1]: #folders-by-kind-instead-of-by-feature
[toc-2]: #name-prefix-standing-in-for-a-directory

## Folders by kind instead of by feature

**Definition.** The top directories sort code by its technical kind
(`components/`, `services/`, `models/`, `controllers/`, `utils/`), so one
feature is spread across all of them and one change edits every one.
The Angular style guide says: "Avoid creating subdirectories based on the
type of code that lives in those directories. For example, avoid creating
directories like `components`, `directives`, and `services`" and to
"Organize your project into subdirectories based on the features of your
application" ([Angular][angular]). The same split is called
package-by-layer against package-by-feature ([javapractices][pbf]).
Robert C. Martin argues that "architectures should tell readers about the
system, not about the frameworks you used in your system"
([Screaming Architecture][screaming]). His Common Closure Principle states
the goal for packages: "A CHANGE THAT AFFECTS A PACKAGE AFFECTS ALL THE
CLASSES IN THAT PACKAGE" ([Granularity][granularity]).

**Use when.**

- One feature's files sit in three or more kind directories, and the
  history shows them changing together (a cross-directory pair in
  `change_coupling.py`).
- A reader cannot tell what the system does from its top directories.

**Do not use when.**

- The framework requires the layout. Rails generates `app/models`,
  `app/controllers`, and `app/views` by convention
  ([Rails guide][rails]). Django groups by app, "a Python package that
  provides some set of features" ([Django][django]), with `models.py` and
  `views.py` inside each app, which is already by feature.
- The project is small enough that one kind directory holds each
  feature's single file.
- The team chose the layout. React "doesn't have opinions on how you put
  files into folders" and names grouping by feature and by file type as
  both common ([React FAQ][react]). Spring Boot "does not require any
  specific code layout to work" ([Spring Boot][spring]). Report the
  coupling cost with numbers instead of calling the choice wrong.

**Example.** Before, one feature in three places:

```text
src/components/InvoiceTable.tsx
src/services/invoiceService.ts
src/models/invoice.ts
```

After, one directory per feature:

```text
src/invoices/InvoiceTable.tsx
src/invoices/invoice-service.ts
src/invoices/invoice.ts
```

**Cost removed.** Opening three directories for one change, and imports
that cross the whole tree for code that belongs together.

**Verify.**

1. `python3 scripts/change_coupling.py --since <date>` lists the
   cross-directory pairs; the report names the feature each pair belongs
   to.
1. After a move, the build and tests pass, and the next scan shows fewer
   cross-directory pairs for that feature.

## Name prefix standing in for a directory

**Definition.** Files in one directory share a growing name prefix, and
the prefix does the job a directory would do. It starts with one file,
`payment.ts`. Then `payment-card.ts` appears, and `payment` has become a
category. Later `payment-card-validation.ts` appears, and `payment-card`
becomes a category inside it. No
catalog names this smell. The Go blog gives the fix for the same pattern
in package contents: "look for types and functions with common name
elements and pull them into their own package" ([Go blog][go-names]).

**Use when.**

- Three or more distinct file stems in one directory share a prefix of
  whole words (the scanner's default; `--min-group` changes it). The
  number 3 is this skill's choice, not a sourced limit.
- A prefix nests: a longer prefix covers a subset of the same files.

**Do not use when.**

- The names differ only by extension or by a test or style companion
  (`widget.ts`, `widget.css`, `widget.spec.ts`). The scanner counts
  distinct stems, so these do not form a group.
- Go files that differ by build suffix (`poll_linux.go`,
  `poll_windows_amd64.go`). The scanner strips `GOOS` and `GOARCH`
  suffixes on `.go` files.
- A directory would be deeper than the team's limit. React suggests
  "limiting yourself to a maximum of three or four nested folders"
  ([React FAQ][react]); report the prefix, and let the team choose.

**Example.** The scanner on a flat directory:

```text
src/payment.ts
src/payment-card.ts
src/payment-card2.ts
src/payment-card-validation.ts
src/payment-card-validation-old.ts
src/payment-refund.ts
```

Output, with long lines wrapped; an indented line continues the one
above it:

```text
$ python3 scripts/layout_smells.py src
numbered-sibling src/payment-card-validation-old.ts: "old" marks a
  leftover version
numbered-sibling src/payment-card2.ts: "payment-card2" repeats
  "payment-card" with a number
prefix-group src: prefix "payment" shared by 6 names: payment,
  payment-card, payment-card-validation, payment-card-validation-old,
  payment-card2, payment-refund
prefix-group src: prefix "payment-card" shared by 4 names: payment-card,
  payment-card-validation, payment-card-validation-old, payment-card2
findings: 4 (prefix-group 2, numbered-sibling 2)
```

The nested groups give the target tree. The numbered and `old` files
need a decision first ([next card](#numbered-and-leftover-copies)): here
`payment-card2` turned out to be saved cards, and the old validation was
unused.

```text
src/payment/payment.ts
src/payment/refund.ts
src/payment/card/card.ts
src/payment/card/saved-card.ts
src/payment/card/validation.ts
```

**Cost removed.** Scanning a long flat listing to find a feature's files,
and names that grow a word each time the feature grows.

**Verify.**

1. `python3 scripts/layout_smells.py <dir>` reports no `prefix-group`
   for the moved files.
1. The build and tests pass, and no file inside the new directory repeats
   the directory name ([stutter](#stutter)).

## Numbered and leftover copies

**Definition.** Files whose names differ from a sibling only by a number
or a version word: `file1`/`file2`, `handler_v2`, `parser_old`,
`report-final2`, `Copy of notes`, and editor or merge leftovers such as
`main.c~`, `main.c.orig`, `main.c.bak`. No catalog names this smell. The
nearest named problems are Duplicated Code
([catalog](smell-catalog.md#duplicated-code)) and copy-and-paste
programming ([Wikipedia][copy-paste]). The number hides what differs
between the files.

**Use when.**

- A numbered file has a sibling with the same base name, or another
  numbered sibling.
- A name contains `old`, `new`, `copy`, `bak`, `orig`, or `final` as a
  word, or ends in a backup suffix.

**Do not use when.**

- The number is part of the name: `sha256`, `http2`, `base64`, `utf8`.
  The scanner reports a number only when a sibling shares the base.
- Versions served together on purpose: `api/v1` and `api/v2` for clients
  that have not moved.
- Ordered files the tool requires: database migrations
  (`0003_add_index.py`), numbered fixtures, and chapter files.

**Example.** `report.py` and `report2.py` both build a sales report;
`report2.py` adds a currency column. Run a duplicate detector
(`jscpd --min-tokens 50 src`, or `pmd cpd --minimum-tokens 50 --dir src`)
to measure the overlap. Report the shared lines, then name the
difference: one `report.py` with a `currency` option, or two files
named for what each is (`sales_report.py`, `fx_sales_report.py`).

**Cost removed.** Edits made to one copy and not the other, and readers
guessing which copy runs.

**Verify.**

1. The report lists each copy with the duplicate detector's count, and
   whether anything imports or runs it (`rg -n 'report2' .`).
1. For leftovers (`~`, `.orig`, `.bak`), `git ls-files` shows whether
   they are tracked; untracked ones belong in `.gitignore`, not in the
   report.

## Dumping-ground and category files

**Definition.** A file or package named for a kind of thing instead of a
concern, which collects unrelated code: `utils`, `helpers`, `common`,
`misc`, `shared`, and repository-wide category files such as `types`,
`constants`, `models`, `enums`, `interfaces`, and `globals`. The Go blog
says: "Packages named util, common, or misc provide clients with no sense
of what the package contains" ([Go blog][go-names]). Google's Go style
lists "util, utility, common, helper, model, testhelper" as uninformative
names ([Google Go][google-go]). Kotlin: "avoid using meaningless words
such as Util in file names" ([Kotlin][kotlin]). Angular: "Avoid overly
generic file names like helpers.ts, utils.ts, or common.ts"
([Angular][angular]).

**Use when.**

- The scanner reports `generic-name` for a file or directory.
- A repository-wide `types.ts` or `constants.py` holds values for
  several unrelated features, so every feature imports it.

**Do not use when.**

- The category file is scoped to one feature: `invoices/types.ts` holds
  only invoice types.
- The framework names the file: a Django app's `models.py`, a Rust crate's
  `lib.rs`, a Rails `app/models/` directory.
- The repository already has the convention and the task is not to change
  it; report it once and move on.

**Example.** A 40-function `utils.py`. Group its functions by the name
elements they share, as the Go blog suggests: `format_money` and
`parse_money` go to `money.py`; `retry_request` and `backoff` go to
`http_retry.py`; `slugify` goes to `text.py`. Count the importers of
each group (`rg -n 'from utils import' src`) to show where each module
belongs.

**Cost removed.** Imports that tell a reader nothing, and a module whose
dependencies grow with every feature. The Go blog adds: "Over time, they
accumulate dependencies that can make compilation significantly and
unnecessarily slower".

**Verify.**

1. The scanner's `generic-name` findings are listed with the number of
   unrelated groups in each file.
1. After a split, each new module's name states what it holds, and its
   importers come from one area.

## Stutter

**Definition.** A name repeats the name of the package, module, or
directory that contains it, so callers read it twice: `http.HTTPServer`,
`chubby.ChubbyFile`, `billing/billingService.ts`. Go: "if you are in
package chubby, you don't need type ChubbyFile, which clients will write
as chubby.ChubbyFile" ([Code Review Comments][go-crc]); "The HTTP server
provided by the http package is called Server, not HTTPServer"
([Go blog][go-names]). Clippy's `module_name_repetitions` "Detects public
item names that are prefixed or suffixed by the containing public
module's name" (in the `restriction` group, so off by default)
([Clippy source][clippy-repetitions]). Clippy's `module_inception`
(`style` group) flags a module with the same name as its parent.

**Use when.**

- The scanner reports `stutter`: a file's stem starts with its
  directory's name followed by more words.
- A type or function repeats its module's name in a language whose
  callers write the module name (Go, Rust, Python modules, Elixir).

**Do not use when.**

- The file name equals the directory name exactly (`widget/widget.go`,
  `hero-list/hero-list.component.ts`). That is a common convention for a
  directory's main file, and the scanner does not report it.
- The language imports names without the module prefix (Java, C#,
  TypeScript named imports), so callers never see the repetition. Report
  it only if the team's style guide asks.

**Example.** `billing/billingService.ts` becomes `billing/service.ts`,
imported as `import { BillingService } from "./billing/service"`. In Go,
`widget.NewWidget` becomes `widget.New` ([Google Go][google-go]).

**Cost removed.** Long names at every call site that repeat what the
import already said.

**Verify.**

1. The scanner reports no `stutter` for the renamed files.
1. The build passes, and the renamed identifiers still read clearly at
   their call sites.

## Crowded and deep directories

**Definition.** A directory with so many files that a listing stops
helping, or paths nested so deep that a reader loses the place. Angular:
"Avoid putting so many files into one directory that it becomes hard to
read or navigate" ([Angular][angular]); it gives no number. React:
"consider limiting yourself to a maximum of three or four nested folders
within a single project" ([React FAQ][react]).

**Use when.**

- The team has a limit, or the user gives one. Run
  `layout_smells.py --max-files N` and `--max-depth N` with it. The
  scanner has no default for either, because no source gives one.

**Do not use when.**

- No limit was chosen. Report the largest directories and the deepest
  paths with their counts, and state that no sourced limit exists.
- The directory is generated, vendored, or a set of fixtures or
  migrations, where a long flat listing is expected.

**Example.**

```sh
# The ten directories with the most tracked files.
git ls-files | awk -F/ 'BEGIN { OFS = "/" } { NF--; print (NF ? $0 : ".") }' |
  sort | uniq -c | sort -rn | head
# Findings against the team's limits.
python3 scripts/layout_smells.py src --max-files 25 --max-depth 5
```

A crowded directory is often a prefix group or a folders-by-kind layout
that has grown. Read the earlier cards before you propose new
subdirectories.

**Cost removed.** Scrolling a listing to find a file, and imports with
many `../` steps.

**Verify.**

1. The report quotes the limit used and who chose it.
1. Each crowded directory is traced to a cause from the earlier cards, or
   reported as crowded with no cause found.

[angular]: https://angular.dev/style-guide
[pbf]: http://www.javapractices.com/topic/TopicAction.do?Id=205
[screaming]: https://blog.cleancoder.com/uncle-bob/2011/09/30/Screaming-Architecture.html
[granularity]: http://web.archive.org/web/2011id_/http://www.objectmentor.com/resources/articles/granularity.pdf
[rails]: https://guides.rubyonrails.org/getting_started.html
[django]: https://docs.djangoproject.com/en/stable/ref/applications/
[react]: https://legacy.reactjs.org/docs/faq-structure.html
[spring]: https://docs.spring.io/spring-boot/reference/using/structuring-your-code.html
[go-names]: https://go.dev/blog/package-names
[google-go]: https://google.github.io/styleguide/go/decisions
[go-crc]: https://go.dev/wiki/CodeReviewComments
[kotlin]: https://kotlinlang.org/docs/coding-conventions.html
[clippy-repetitions]: https://github.com/rust-lang/rust-clippy/blob/master/clippy_lints/src/item_name_repetitions.rs
[copy-paste]: https://en.wikipedia.org/wiki/Copy-and-paste_programming
