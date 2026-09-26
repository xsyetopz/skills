# Documentation content

What to write, for which reader. The example project is
[`assets/examples/wordfreq/`][example]. Its README and CONTRIBUTING
commands are executed by `scripts/check_doc_commands.py` in
`assets/verify.sh`.

## Contents

- README lead and quick start
- Prerequisites from the manifests
- Commands with stated directory and expected output
- CONTRIBUTING around the change path
- Match the page to the reader's task
- API reference from the source of truth
- Decision records only for real decisions
- Scope boundaries

## README lead and quick start

**Definition.** A README opens with one sentence on what the project
does. A quick start follows: the prerequisites, the smallest command
that produces a useful result, and that result.

**Use when.** Writing or restructuring a README.

**Do not use when.** The request is formatting only. Keep the existing
structure, and see [formatting-only edits][format].

**Example.** From the example README:

````markdown
wordfreq prints the most frequent words in text files, one count and
word per line.

## Quick start

Requires Python 3.10 or later. From this directory:

```sh
python3 wordfreq.py --top 2 sample.txt
```

Expected output:

```text
3 the
2 dog
```
````

**Cost removed.** Readers who cannot tell what the project does, or who
reach a first result only after reading every section. Check: a new
reader runs the quick start and gets the shown output.

**Verify.**

1. `python3 scripts/check_doc_commands.py README.md` reports
   `output matches` for the quick start.

## Prerequisites from the manifests

**Definition.** Versions and tools named in the docs come from the
project's own files: `pyproject.toml` `requires-python`,
`package.json` `engines`, `rust-toolchain.toml`, `go.mod`, CI matrices.
Never from memory, and never from another project.

**Use when.** Stating supported versions, tools, or platforms.

**Do not use when.** The manifest is silent. Say it is unstated, or ask.
Do not invent a floor.

**Example.**

```sh
rg -n 'requires-python|"engines"|^go |channel' \
  pyproject.toml package.json go.mod rust-toolchain.toml
```

**Cost removed.** Setup failures from versions the project does not
support.

**Verify.**

1. Every version in the docs appears in a manifest or CI file, and the
   report cites the line.

## Commands with stated directory and expected output

**Definition.** Each documented procedure states:

- the working directory;
- the exact command, in a fenced `sh` block;
- the required environment;
- the expected output, in a following `text` block introduced by
  "Expected".

Commands and output are separate blocks, or a `console` block whose
command lines start with a `$` prompt.

**Use when.** Every command in user-facing docs.

**Do not use when.** The command is destructive or publishes something
(deploy, release). Mark the block with `<!-- doc-check: skip -->`,
verify its flags against `--help`, and report it as not run.

**Example.** The broken README documents `--limit`. The checker
reports:

```text
FAIL README.broken.txt:10: python3 wordfreq.py --limit 2 sample.txt
  exit 2: usage: wordfreq [-h] [-n TOP] [files ...] | wordfreq: error:
  unrecognized arguments: --limit
```

The fix is to document the real flag, `--top`. Do not add `--limit` to
the program; that is a code change nobody asked for.

**Cost removed.** Documented flags that do not exist, and outputs that no
longer match. The checker's pass count measures this.

**Verify.**

1. `check_doc_commands.py FILE.md` exits 0. The commands run in a
   temporary copy, so they cannot change the checkout.

## CONTRIBUTING around the change path

**Definition.** A contributing guide gives the steps a change goes
through:

- setup, and the focused and full check commands, taken from the
  repository's automation;
- how to file a useful issue or PR;
- links to the existing security and licence policy.

**Use when.** Writing or updating CONTRIBUTING.

**Do not use when.** The repository has no such policy. Do not invent a
DCO, CLA, code of conduct, or disclosure program.

**Example.** The example CONTRIBUTING documents one check that the
checker runs:

```sh
python3 -m unittest discover -s tests
```

`assets/CONTRIBUTING.template.md` gives the section layout.

**Cost removed.** PRs that fail CI on checks no guide mentioned.

**Verify.**

1. The documented check commands match the CI configuration and pass
   under `check_doc_commands.py`.

## Match the page to the reader's task

**Definition.** Diátaxis names four kinds of page:

- a tutorial, for learning;
- a how-to guide, for a task;
- a reference, for facts;
- an explanation, for reasons.

Each page serves one of them ([Diátaxis][diataxis]).

**Use when.** A page mixes a walkthrough with exhaustive options, or
design history with setup steps.

**Do not use when.** The project is small. One README with sections is
fine; do not create four directories.

**Example.** The example README keeps the quick start short, and puts
the option table under "Options" as reference.

**Cost removed.** Reference detail buried in a quick start.

**Verify.**

1. Each section can be named by one of the four purposes.

## API reference from the source of truth

**Definition.** Generate API reference from its authoritative source:
docstrings with pydoc or Sphinx autodoc, rustdoc, TypeDoc, godoc, or a
checked-in OpenAPI or protobuf file. Edit the source, then regenerate
with the project's command.

**Use when.** Documenting functions, endpoints, or messages.

**Do not use when.**

- Hand-editing generated files.
- Inventing an OpenAPI file for a non-HTTP interface.

**Example.**

```sh
python3 -m pydoc wordfreq | head -n 5
```

**Cost removed.** Reference pages that drift from the code.

**Verify.**

1. After the change, the regeneration command leaves no diff:
   `git diff --exit-code docs/api`.

## Decision records only for real decisions

**Definition.** An ADR records one decision that was made: its context,
the decision, the alternatives, and the consequences, in the
repository's existing ADR format.

**Use when.** A choice was made that future readers will question.

**Do not use when.**

- Recording a proposal as accepted.
- Inventing statuses, approvers, or numbering.

**Example.**

```markdown
# 3. Store counts in memory

Context: inputs are under 100 MB in every documented use.
Decision: keep a Counter in memory instead of an on-disk index.
Alternatives: SQLite index (rejected: adds a dependency for no measured need).
Consequences: inputs larger than RAM are unsupported; the README says so.
```

**Cost removed.** Repeated debates about settled choices.

**Verify.**

1. The decision matches the current code. The ADR names who decided only
   if the user said so.

## Scope boundaries

**Definition.** Changelogs belong to `$update-changelogs`. Agent
instruction files (AGENTS.md, CLAUDE.md) belong to `$write-agents-md`.
Code comments and names belong to `$write-readable-code`.

**Use when.** A request mentions those files.

**Do not use when.** No exception.

**Example.** "Document the new flag in the README and add a changelog
entry." Edit the README here, and write the changelog entry with the
changelog skill.

**Cost removed.** Formats written without their dedicated rules.

**Verify.**

1. Each changed file falls under this skill, or the report names the
   skill used for it.

[example]: ../assets/examples/wordfreq/README.md
[format]: markdown-and-checks.md#formatting-only-edits
[diataxis]: https://diataxis.fr/
