---
name: format-github-markdown
description: >-
  Fixes Markdown that breaks on GitHub or in markdownlint: anchors after a
  heading rename, links after a move, stale tables of contents, tables with
  pipes, alerts and details blocks that show as raw text, and lines over
  MD013. Use when docs render wrong or lint fails. Not for doc content such as
  READMEs or ARCHITECTURE.md.
when_to_use: >-
  Add a table of contents to docs/guide.md and keep it in sync. Links to
  #setup-options are broken on GitHub. Add a NOTE alert and a collapsible
  section. markdownlint fails MD013. A table renders as plain text.
---

# Format GitHub Markdown

Make Markdown render on GitHub as written and pass the repository's linter, without changing what
the page says.

## Rules

- Link only to a heading that exists, and compute its anchor with GitHub's rules, never by guess.
  After renaming a heading or moving a file, search for the old anchor and path
  (`rg -n '#old-anchor|old/path'`) and fix every hit.
- Check links and anchors across files with `check_links.py` from `$write-project-readme`;
  markdownlint MD051 checks one file only.
- Generate a Contents list with `scripts/markdown_toc.py`, not by hand, because hand-written lists
  go stale when headings change.
- Wrap paragraphs with `scripts/reflow_markdown.py`, not by hand; it fills lines to the configured
  width without breaking lists, tables, or code.
- Keep the repository's Markdown linter and config, and never loosen or disable a rule to pass. With
  no markdownlint config, copy [`.markdownlint.jsonc`](assets/markdownlint/.markdownlint.jsonc) and
  [`.markdownlint-cli2.jsonc`](assets/markdownlint/.markdownlint-cli2.jsonc) to the root. With one,
  ask whether to replace it with these templates or keep it, and keep it until the user answers.
- Write headings in title case for the document's language. In English, capitalize the first and
  last word and every other word except articles (*a*, *an*, *the*), coordinating conjunctions
  (*and*, *but*, *for*, *nor*, *or*, *so*, *yet*), prepositions of any length (*of*, *to*,
  *between*, *through*), *as*, and *is*: "Decompile to Matching C". Capitalize a preposition that
  belongs to a phrasal verb ("Set Up the Build"). Other languages have their own rules: French,
  Spanish, Italian, and Polish capitalize only the first word and names, and German capitalizes
  every noun. Follow the convention of the language the user writes in, not the English rule. Keep
  names as their owners write them (`objdiff`, iOS, decomp.me). Anchors are lower-case, so a case
  change keeps links working, but rerun `scripts/markdown_toc.py` for the Contents text.
- Change syntax and heading case only. Leave the wording, facts, and commands of the page as they
  are, unless the user asked for a content change.
- When the rendered page cannot be viewed, say so instead of claiming it renders.

## Workflow

1. Run the repository's markdownlint and the checks below on the files, and note each finding.
1. Read [GitHub Markdown](references/github-markdown.md) for the syntax involved.
1. Fix the findings, regenerate Contents lists, and reflow.
1. Rerun the checks until they pass.
1. In the reply, list what was run and what was not checked, such as rendering or external URLs.

## Scripts

Run these from the skill directory or by full path. On Windows, use `py -3` for `python3`.

- `python3 scripts/markdown_toc.py [--check] [--max-level N] [--width N] FILE...` rebuilds the list
  under an existing `## Contents` heading with correct anchors. `--check` only reports a stale list.
  Exit 0 current, 1 stale under `--check`, 2 bad input.
- `python3 scripts/reflow_markdown.py [--check] [--width N] FILE...` refills paragraph lines up to
  MD013 `line_length` from the nearest markdownlint config (100 without one); other blocks and
  paragraphs with hard breaks stay as written. Exit 0 current or rewritten, 1 needs reflow under
  `--check`, 2 bad input or config.
- Tests: `python3 -m unittest discover -s scripts`.

## References

- Read [GitHub Markdown](references/github-markdown.md) when writing anchors, tables, alerts,
  collapsed sections, code fences, diagrams, or a Contents list.
