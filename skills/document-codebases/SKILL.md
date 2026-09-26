---
name: document-codebases
description: >-
  Writes and fixes repository documentation (README, CONTRIBUTING, guides, API
  reference, ADRs), runs every documented command, and checks links. Use when
  docs are missing, wrong, or out of date. Not for changelogs or agent
  instruction files.
---

# Document Codebases

Write docs whose commands run and whose links resolve, stating every
version, flag, and output as the project actually has it.
`assets/verify.sh` runs the bundled scripts on the example project.

## Workflow

1. Identify the reader and the task: first use, contributing, lookup,
   or understanding a design ([page purpose][purpose]).
1. Read the sources: manifests for versions, the CLI's `--help` or
   parser for flags, the CI configuration for check commands, and the
   code for behavior ([prerequisites][prereqs]).
1. Write each procedure as directory, command, and expected output
   ([commands][commands]). Mark destructive or publishing commands
   `<!-- doc-check: skip -->`.
1. Run `python3 scripts/check_doc_commands.py FILE.md` and fix what it
   reports.
1. Run `python3 scripts/check_links.py` on the changed files, then the
   repository's Markdown linter.
1. For formatting-only requests, run
   `python3 scripts/same_words.py OLD NEW` ([formatting][formatting]).
1. Report: the commands executed and their results, the links checked,
   what was not run (skipped blocks, rendering, external links), and
   why.

## Route the task to a card

| Task | Card |
| --- | --- |
| New or restructured README | [README lead and quick start][readme] |
| Versions or tools in docs | [Prerequisites][prereqs] |
| Any command in docs | [Commands][commands] |
| CONTRIBUTING | [Change path][contributing] |
| Page mixes tutorial and reference | [Page purpose][purpose] |
| API docs | [API reference from source][api] |
| Record a design decision | [ADR][adr] |
| Moved or renamed files, broken anchors | [Links and anchors][links] |
| Accessibility of links and images | [Link text and alt text][alt] |
| Code blocks | [Fenced code][fences] |
| Tables, alerts, details, task lists | [GFM features][gfm] |
| Diagrams | [Mermaid][mermaid] |
| "Just fix the formatting" | [Formatting-only edits][formatting] |
| Lint | [Markdown lint][lint] |
| Changelog, AGENTS.md, code comments | [Scope boundaries][scope] |

## Rules

- Every documented command either runs under `check_doc_commands.py`,
  or is marked skip with a reason in the report.
- Versions, flags, paths, and outputs come from this repository's
  files and runs, never from memory or another project.
- When docs and code disagree, fix the docs unless the user asked for a
  code change.
- A formatting-only edit changes no word, URL, or code line.
  `same_words.py` must pass.
- Do not invent policies: CLA, DCO, code of conduct, security contacts,
  SLAs, or support channels.
- Do not hand-edit generated reference. Change the source, and
  regenerate.
- Lint passing proves only syntax and style. Keep the repository's
  linter and config, and do not loosen its rules.

## Bundled tools

- `scripts/check_doc_commands.py FILE.md [--cwd DIR] [--list]` runs the
  commands in `sh`, `bash`, `shell`, and `console` blocks in a
  temporary copy, and compares the output with the following "Expected"
  `text` block.
- `scripts/check_links.py PATH... [--external]` checks relative links,
  GitHub anchors, reference definitions, vague link text, and empty alt
  text.
- `scripts/same_words.py BEFORE AFTER` checks that a formatting-only
  edit kept the same words and code.
- `scripts/test_doc_tools.py` tests the three scripts.
- `assets/examples/wordfreq/`: a CLI with a correct README and
  CONTRIBUTING, plus `README.broken.txt`, which has a wrong flag, a wrong
  anchor, and a missing file.
- `assets/repository-overview.template.md`,
  `assets/CONTRIBUTING.template.md`, and `assets/.markdownlint-cli2.jsonc`.
- `sh assets/verify.sh`.

## References

- [Documentation content](references/content.md)
- [Markdown and checks](references/markdown-and-checks.md)

## Completion evidence

- `check_doc_commands.py` output for each changed file, and every
  skipped block with its reason.
- `check_links.py` output with 0 errors, and the linter's result.
- For formatting-only work, the `same_words.py` result.
- Sources for each version or flag stated in the docs.
- What was not checked: rendering on the target, external URLs, and
  commands that are destructive.

## Stop and ask

- The docs describe behavior the code does not have, and it is unclear
  whether the docs or the code are wrong.
- A procedure can only be verified by deploying, publishing, or using
  real credentials.
- The request would add policy statements the repository has not
  adopted.

[readme]: references/content.md#readme-lead-and-quick-start
[prereqs]: references/content.md#prerequisites-from-the-manifests
[commands]: references/content.md#commands-with-stated-directory-and-expected-output
[contributing]: references/content.md#contributing-around-the-change-path
[purpose]: references/content.md#match-the-page-to-the-readers-task
[api]: references/content.md#api-reference-from-the-source-of-truth
[adr]: references/content.md#decision-records-only-for-real-decisions
[scope]: references/content.md#scope-boundaries
[links]: references/markdown-and-checks.md#relative-links-and-heading-anchors
[alt]: references/markdown-and-checks.md#link-text-and-image-alt-text
[fences]: references/markdown-and-checks.md#fenced-code-with-language-tags
[gfm]: references/markdown-and-checks.md#tables-task-lists-alerts-and-details
[mermaid]: references/markdown-and-checks.md#mermaid-diagrams
[formatting]: references/markdown-and-checks.md#formatting-only-edits
[lint]: references/markdown-and-checks.md#markdown-lint-with-the-repositorys-config
