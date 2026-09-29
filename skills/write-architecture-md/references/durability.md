# Durability and upkeep

How an ARCHITECTURE.md stays true after the code moves. The rules come
from matklad's original post ([ARCHITECTURE.md][matklad], 2021-02-06) and
the architecture.md generator prompt ([`prompt.md`][prompt] at commit
`fed7705`). `scripts/check_architecture.py` detects the mechanical
failures; the rest is checked by reading.

## Contents

- Name files and symbols, do not link them
- Self-contained
- Durable facts only
- Updating an existing ARCHITECTURE.md
- Placement and neighboring documents

## Name files and symbols, do not link them

**Definition.** Refer to code by path in backticks and by symbol name
(`LinkStore.resolve`), without Markdown links to local files and without
line numbers. matklad: "Do name important files, modules, and types. Do
not directly link them (links go stale)." Readers find the name with
symbol search.

**Use when.** Every reference to code in the document.

**Do not use when.** The target is outside the repository and stable:
a specification, a pinned upstream commit, a hosted service's docs. Link
those.

**Example.**

```markdown
`LinkStore.resolve` in `shortlinks/store.py` returns `None` for unknown
codes.
```

Not a Markdown link to `shortlinks/store.py` with an `#L20` anchor, and not
`shortlinks/store.py:20`.

**Cost removed.** Line numbers are wrong after the next edit above them,
and relative links break when the document is rendered somewhere else
(a docs site, a pasted prompt). A path plus a name survives both.

**Verify.**

1. The checker warns on each relative local link and each `file:line`
   reference, and errors on each named path that does not exist.
1. `rg -n 'LinkStore|def resolve'` for each named symbol.

## Self-contained

**Definition.** The document states its facts instead of pointing to
other files for them. The prompt: "The file must be entirely
self-contained. Do not say 'see X file' as a substitute for explanation."

**Use when.** A section's content lives in another document (setup in
CONTRIBUTING.md, deployment in a runbook). Summarize the architectural
fact here in one or two sentences.

**Do not use when.** The other document is the owner of a long procedure
that does not describe architecture. Summarize the fact, then name the
owner as a secondary pointer: "Releases are tagged by CI from `main`; the
release checklist is in `RELEASING.md`."

**Example.**

```markdown
Tests run with `python3 -m unittest discover -s tests -t .` from the
repository root; they start a real HTTP server on a free port.
```

Not: "See CONTRIBUTING.md for how to run tests."

**Cost removed.** An agent that loads only ARCHITECTURE.md (a common
context-budget choice) otherwise gets a pointer and no fact.

**Verify.**

1. The checker warns on "see/refer to/described in `X.md`" phrases.
1. Read each remaining mention of another document: the fact must be
   stated before the pointer.

## Durable facts only

**Definition.** Include what is unlikely to change between releases:
responsibilities, boundaries, data ownership, invariants, the shape of
the main flows. matklad: "only specify things that are unlikely to frequently
change." Leave out counts, versions below the major, per-function
behavior, and anything a test already pins.

**Use when.** Deciding whether a sentence belongs. Ask: would a
refactor that keeps the architecture make it false?

**Do not use when.** The detail is a constraint an agent must respect,
such as a supported runtime floor ("Python 3.10 or later") or a protocol
version. State those; they change rarely and cost a lot when missed.

**Example.**

```markdown
Only `store.py` imports `sqlite3`; the HTTP layer never touches the
database directly.
```

Not: "`store.py` has 34 lines and two methods."

**Cost removed.** Documents that go stale in weeks and then teach wrong
facts. matklad recommends revisiting the file "a couple of times a
year"; that cadence works only if the content is durable.

**Verify.**

1. For each sentence with a number, a version, or a count, decide whether
   a refactor that keeps the architecture would change it. Remove it if
   so.
1. Tension check: the eleven template sections make the file longer than
   matklad's "short" ideal. Keep each section to its facts; a one-line
   "Not evident from the repository." is complete.

## Updating an existing ARCHITECTURE.md

**Definition.** A drift audit: compare every path, symbol, command,
component, and technology in the current document against the tree, then
edit only what changed and update the date.

**Use when.** An ARCHITECTURE.md exists and the task is to refresh it,
or a change renamed, moved, split, or removed a component it names.

**Do not use when.** The existing file follows a different structure the
project chose on purpose (matklad's bird's-eye plus codemap form, as in
rust-analyzer). Keep that structure and fix the facts; do not force the
eleven template sections on it unless the user asks. Run the checker for
paths only and ignore its missing-section errors.

**Example.** After `handlers.py` was renamed to `http.py`:

```sh
python3 scripts/check_architecture.py ARCHITECTURE.md
git log --since=2026-03-01 --name-status --diff-filter=RD -- . | head
```

The first reports `names shortlinks/handlers.py, which does not exist`;
the second lists the rename; the edit replaces the name everywhere and
sets the new date.

**Cost removed.** Stale paths that send agents to deleted files, and
rewrites that discard correct project-specific content.

**Verify.**

1. The checker reports no missing paths and no uncovered top-level
   directory.
1. `git diff --stat ARCHITECTURE.md` shows edits only in sections whose
   facts changed, plus the date.
1. Every command in the document ran after the edit.

## Placement and neighboring documents

**Definition.** ARCHITECTURE.md explains how the system is built: the
map, the boundaries, the flows. The README says what the project is and
how to use it; AGENTS.md or CLAUDE.md gives agents commands and rules;
ADRs record one decision each with its context; CONTRIBUTING.md holds
the workflow for contributors.

The file is `ARCHITECTURE.md`, capitalised, at the repository root. The
prompt asks for "an ARCHITECTURE.md file in the project root"; matklad
puts it "next to README and CONTRIBUTING". A monorepo with independent
systems may add one per system root, each named `ARCHITECTURE.md`.

**Use when.** Deciding where a fact goes, and where the file lives. When
the architecture is kept elsewhere (`docs/architecture.md`), move it:
`git mv docs/architecture.md ARCHITECTURE.md`, then update every
reference to the old path and fix the facts as in the updating card.

**Do not use when.** The project publishes architecture on a docs site
built from another tree. Keep that page, and make the root
`ARCHITECTURE.md` the source it is built from or points to; do not keep
two documents with the same facts.

**Example.**

- "Run `just test` before committing" goes in AGENTS.md.
- "`http.py` never imports `sqlite3`" goes in ARCHITECTURE.md.
- "We chose SQLite over PostgreSQL because deployment is a single host"
  goes in an ADR; ARCHITECTURE.md states the choice and, if documented,
  one line of the reason.

**Cost removed.** Duplicate facts in several files that disagree after
one is updated, and a document readers do not find because it is not
where the name says.

**Verify.**

1. `fd -i -d 3 'architecture|adr|decisions'` before creating a new file;
   afterwards it lists one architecture document, `ARCHITECTURE.md` at
   the root (plus ADRs).
1. `rg -n 'docs/architecture' --glob '!CHANGELOG.md'` finds no reference
   to the old path. The checker errors on a file not named
   `ARCHITECTURE.md` or kept in `docs/`.
1. `rg -n 'sqlite|redis' README.md AGENTS.md` (the project's own terms):
   facts shared with another document agree with it.

[matklad]: https://matklad.github.io/2021/02/06/ARCHITECTURE.md.html
[prompt]: https://github.com/timajwilliams/architecture/blob/fed7705ccb5b90980fae624fc30f21a1f45655ac/prompt.md
