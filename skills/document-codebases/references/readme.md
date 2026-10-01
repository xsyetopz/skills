# README, CONTRIBUTING, and other project docs

## Contents

- [README](#readme)
- [Commands and expected output](#commands-and-expected-output)
- [Versions and prerequisites](#versions-and-prerequisites)
- [CONTRIBUTING](#contributing)
- [API reference](#api-reference)
- [Decision records](#decision-records)
- [Moved or renamed files](#moved-or-renamed-files)

## README

- Open with one sentence saying what the project does, then a quick start:
  prerequisites, the smallest command that gives a useful result, and that
  result. A reader who cannot run the quick start stops reading.
- Put the install and first-run path before features, badges, or history.
- Link to deeper docs instead of copying them. Copies drift.
- Do not write roadmaps, "coming soon" notes, or planned flags. Docs
  describe what the code does now.

## Commands and expected output

- State the directory a command runs from and show the output a reader
  should see, as a `text` block after the command.
- `scripts/check_doc_commands.py` runs `sh`, `bash`, `shell`, and `console`
  blocks in a temporary copy and compares output with a following block
  introduced by the word "Expected".
- Mark destructive, publishing, network, or credentialed commands with
  `<!-- doc-check: skip -->` on the line before the fence, and tell the
  user they were not run.
- For a CLI, take flags from `--help` or the argument parser, never from
  memory of a similar tool.

```console
$ python3 tool.py --top 2 sample.txt
3 the
2 dog
```

## Versions and prerequisites

Take versions from the project's own files: `requires-python` in
`pyproject.toml`, `engines` in `package.json`, `rust-toolchain.toml`,
`go.mod`, and the CI matrix. When two of them disagree, report it instead
of picking one. Name the package manager the lockfile implies.

## CONTRIBUTING

Organize it around the change path: set up, run the tests, run the
linters, open a change. Copy the check commands from CI configuration so
a contributor runs what CI runs. Do not add a CLA, DCO, code of conduct,
security contact, response-time promise, or support channel the repository
has not adopted.

## API reference

Generate it from the source (docstrings, OpenAPI, `--help`) and document
how to regenerate it. Do not hand-edit generated output: the next run
overwrites it. When a signature and its doc disagree, the code is right.

## Decision records

Write an ADR only for a real decision with alternatives: context, decision,
consequences. Do not invent rationale for old code. Write "rationale not
documented" instead.

## Moved or renamed files

After a move, search for the old path and old heading anchors across the
repository (`rg -n 'old/path|#old-anchor'`), fix each hit, then run
`scripts/check_links.py` on the docs directory. Keep one copy of a moved
doc, not two.
