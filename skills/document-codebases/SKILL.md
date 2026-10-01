---
name: document-codebases
description: >-
  Writes README, ARCHITECTURE.md, and GitHub Markdown docs that match the
  code, with working commands, links, and contents lists. Use when writing or
  fixing project docs.
---

# Document Codebases

Write docs a reader can follow without asking: every command runs, every link resolves, and every
statement matches the code as it is today.

## Rules

- Do not run a destructive, publishing, network, or credentialed command, in a draft or an existing
  doc, without the user's approval; mark its block skip. Run every other command before writing it
  into a doc, from the directory the doc states, and show its output; commands written from memory
  fail for readers. For an existing doc, list its blocks first with
  `python3 scripts/check_doc_commands.py FILE.md --list`.
- Take versions, flags, paths, and outputs from this repository's manifests, CI configuration,
  `--help`, and code, never from another project or from memory.
- Describe what the code does now. Leave out plans, roadmaps, and "coming soon" flags, because
  readers act on docs as fact.
- When docs and code disagree, fix the docs unless the user asked for a code change. Report the
  disagreement if it is unclear which is wrong.
- Do not invent policy: CLA, DCO, code of conduct, security contacts, response times, support
  channels.
- Do not hand-edit generated reference. Change the source and regenerate.
- ARCHITECTURE.md names modules, their boundaries, invariants, and entry points (a codemap). It is
  not a file-by-file listing, a tour of dependencies, or a template with every section filled.
  Anything the code does not show is left out.
- Mark skipped blocks `<!-- doc-check: skip -->` and say in the reply they were not run.
- After renaming a heading or moving a file, search for the old anchor and path and fix every link.
  Anchors and relative links break silently.
- Keep the repository's Markdown linter and config, and never loosen a rule to pass. With no
  markdownlint config, copy [`.markdownlint.jsonc`](assets/markdownlint/.markdownlint.jsonc) and
  [`.markdownlint-cli2.jsonc`](assets/markdownlint/.markdownlint-cli2.jsonc) to the root. With one,
  ask whether to replace it with these templates or keep it, and keep it until the user answers.
- Wrap paragraphs with `scripts/reflow_markdown.py`, not by hand; it fills lines to the configured
  width without breaking lists, tables, or code.
- Leave changelogs, AGENTS.md, code comments, and SKILL.md files to their own skills.

## Workflow

1. Name the reader and the task: first use, contributing, lookup, or understanding the design. One
   page serves one of these.
1. Read the sources for every fact the page will state.
1. Write the page. Put the quick start or the map first.
1. Run the commands and the checks below, fix the findings, and rerun.
1. In the reply, list what was run, what was skipped and why, and what was not checked, such as
   rendering or external URLs.

## Scripts

Run these from the skill directory or by full path. On Windows, use `py -3` for `python3`.

- `python3 scripts/check_doc_commands.py FILE.md [--cwd DIR] [--list] [--json]` runs `sh`, `bash`,
  `shell`, and `console` blocks with POSIX `sh` (Git Bash or WSL on Windows) in a temporary copy and
  compares output with the block after "Expected". Exit 0 all passed, 1 a command failed or output
  differed, 2 bad input.
- `python3 scripts/check_links.py PATH... [--external] [--json]` checks relative links, GitHub
  heading anchors, reference definitions, vague link text, and empty alt text. Exit 0 clean, 1
  errors, 2 bad input.
- `python3 scripts/check_architecture.py ARCHITECTURE.md [--json | --commands]` checks the file name
  and placement, empty sections, placeholders, tree and backticked paths that do not exist,
  undescribed top-level directories, and warns on local links and `file:line` references.
  `--commands` lists the commands to run. Exit 0 no errors, 1 errors, 2 bad input. It cannot detect
  invented technology; search the code for each one instead.
- `python3 scripts/markdown_toc.py [--check] [--max-level N] [--width N] FILE...` rebuilds the list
  under an existing `## Contents` heading with correct anchors. `--check` only reports a stale list.
  Exit 0 current, 1 stale under `--check`, 2 bad input.
- `python3 scripts/reflow_markdown.py [--check] [--width N] FILE...` refills paragraph lines up to
  MD013 `line_length` from the nearest markdownlint config (100 without one); other blocks and
  paragraphs with hard breaks stay as written. Exit 0 current or rewritten, 1 needs reflow under
  `--check`, 2 bad input or config.
- Tests: `python3 -m unittest discover -s scripts`.

## References

- Read [README and project docs](references/readme.md) when writing a README, CONTRIBUTING, API
  reference, or ADR, or when files moved.
- Read [ARCHITECTURE.md](references/architecture.md) when creating, updating, or auditing an
  ARCHITECTURE.md.
- Read [GitHub Markdown](references/github-markdown.md) when writing anchors, tables, alerts,
  collapsed sections, code fences, or a Contents list.
