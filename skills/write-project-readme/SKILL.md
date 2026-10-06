---
name: write-project-readme
description: >-
  Writes and fixes README, CONTRIBUTING, getting-started, and API docs whose commands run,
  with versions and flags taken from manifests, CI, and help output, and real output.
  Use when docs are missing, install steps fail, or a documented flag no longer exists.
  Not for ARCHITECTURE.md or changelogs.
---

# Write Project README

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
- Mark skipped blocks `<!-- doc-check: skip -->` and say in the reply they were not run.
- After moving a file, search for the old path and anchors and fix every link, then run
  `scripts/check_links.py`. Relative links break silently.
- Write headings in the title case of the document's language, as `$format-github-markdown`
  describes ("Install from Source" in English).
- Leave ARCHITECTURE.md to `$write-architecture-md`, Markdown syntax, Contents lists, and line
  wrapping to `$format-github-markdown`, and changelogs, AGENTS.md, code comments, and SKILL.md
  files to their own skills.

## Workflow

1. Name the reader and the task: first use, contributing, or lookup. One page serves one of these.
1. Read the sources for every fact the page will state.
1. Write the page. Put the quick start first.
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
- Tests: `python3 -m unittest discover -s scripts`.

## References

- Read [README and project docs](references/readme.md) when writing a README, CONTRIBUTING, API
  reference, or ADR, or when files moved.
