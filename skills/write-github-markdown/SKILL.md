---
name: write-github-markdown
description: >-
  Writes and fixes GitHub Flavored Markdown with working anchors, linked
  contents lists, fences, tables, and alerts. Use when writing or reviewing
  Markdown for GitHub. Not for deciding which docs a repo needs.
---

# Write GitHub Markdown

Write Markdown that renders correctly on GitHub and reads correctly as raw
text, because agents read the source, often only its first lines or one
section. Syntax follows the GitHub Flavored Markdown spec ([GFM][gfm]) and
GitHub's writing docs ([basic syntax][basic]); rules are checked with the
project's markdownlint configuration.

## Workflow

1. Read the project's Markdown lint config and one or two existing files.
   Their conventions (list marker, line length, heading style) win over
   the defaults in the cards.
1. Outline with headings first: one `#` title, then `##` sections whose
   titles say what the section holds ([headings][headings]).
1. Write the body with the card for each construct in the table below.
1. For a file over 100 lines, or when asked for a table of contents, add a
   `## Contents` heading after the intro and run
   `python3 scripts/markdown_toc.py FILE.md` ([Contents][toc]).
1. Check every `#anchor` and relative link against the target file
   ([anchors][anchors], [relative links][relative]).
1. Run the project's Markdown linter and
   `python3 scripts/markdown_toc.py --check` on files with a Contents
   list, and fix what they report ([lint map][lint]).
1. For alerts, task lists, footnotes, math, or Mermaid, render the file
   with `gh api markdown` in `gfm` mode, not the default `markdown` mode
   ([renderers][renderers]). When the final page cannot be viewed, ask
   the user to open it on GitHub instead of guessing.
1. Report the commands, their exit status, and what was not checked.

## Route the task to a card

| Task | Card |
| --- | --- |
| Heading levels and titles | [Headings as the outline][headings] |
| Link to a section, or a broken anchor | [Section links][anchors] |
| Table of contents | [Linked Contents list][toc] |
| Anchor that must survive a heading rename | [Custom anchors][custom] |
| Link to another file in the repository | [Relative links][relative] |
| Long URLs or repeated links | [Reference-style links][refs] |
| Images and alt text | [Images with alt text][images] |
| Issue, commit, and user references | [Autolinked references][autolinks] |
| Code blocks | [Fenced code with a language][fences] |
| Code block that shows a code block | [Nested fences][nested] |
| Tables, alignment, pipes in cells | [Tables][tables] |
| Table or a list | [Table or list][table-or-list] |
| Nested and ordered lists | [Lists and nesting][lists] |
| Checklists | [Task lists][tasks] |
| Hard line breaks | [Line breaks][breaks] |
| Literal `*`, `_`, `#`, or `<` | [Backslash escapes][escapes] |
| Notes to editors | [HTML comments][comments] |
| Where the file will be rendered | [GitHub and other renderers][renderers] |
| Note, tip, warning boxes | [Alerts][alerts] |
| Footnotes | [Footnotes][footnotes] |
| Long optional detail | [Collapsed sections][details] |
| Diagrams | [Mermaid diagrams][mermaid] |
| Formulas | [Math expressions][math] |
| File read raw by an agent | [Raw text reads][raw] |
| Centered logos, badges, layout HTML | [No decorative HTML][html] |
| Lint messages | [Lint rule map][lint] |
| Which docs to write and what they say | `$document-codebases` |

## Rules

- One `#` heading per file, levels increase one at a time, and no bold
  line stands in for a heading.
- Every table of contents is a list of links to heading anchors, written
  by `markdown_toc.py`, never a plain list of titles.
- Every `#anchor` matches a heading's GitHub anchor: lower-case, markup
  and punctuation other than `-` and `_` removed, spaces to `-`, and
  `-1`, `-2` on repeats.
- Link to files in the repository with relative paths, not
  `github.com/.../blob/main/...` URLs.
- Every fenced block names a language; use `text` for plain output.
- Link text says where the link goes; no "here" or "this link".
- Images have alt text that says what the image shows.
- Use GitHub-only syntax (alerts, footnotes, Mermaid, math,
  `<details>`) only where the file is read on GitHub; say which renderer
  was assumed.
- Keep the project's lint config; do not disable or relax a rule to make
  a file pass.

## Bundled tools

- `scripts/markdown_toc.py [--check] [--max-level N] [--width N]
  FILE...`: rebuilds the list under an existing `## Contents` heading
  from headings of levels 2 to `--max-level` (default 2), with GitHub
  anchors and repeats numbered. Headings in fenced code are ignored. An
  entry longer than `--width` (default 80) becomes a `[Title][toc-N]`
  reference link with its `[toc-N]: #anchor` definition after the list,
  because markdownlint's MD013 exempts definition lines. The tool owns
  the `toc-` label prefix. Exit 0 current or rewritten, 1 `--check`
  found a stale list, 2 bad input (missing file, no Contents heading, or
  prose inside the Contents section); other files are still processed.

## References

- [Headings and links](references/headings-and-links.md): outline,
  anchors, linked Contents lists, custom anchors, relative and
  reference-style links, images, and autolinked references.
- [Blocks and lists](references/blocks-and-lists.md): fences, nested
  fences, tables, lists, task lists, line breaks, escapes, and HTML
  comments.
- [GitHub extensions](references/github-extensions.md): renderer
  differences, alerts, footnotes, collapsed sections, Mermaid, and math.
- [Agent-readable Markdown and lint](references/agent-readable-and-lint.md):
  raw-text readability, headings as navigation, decorative HTML, and the
  markdownlint rule map.

## Completion evidence

The report lists: the files changed; the linter command and its exit
status; the `markdown_toc.py --check` result for files with a Contents
list; the anchors and relative links checked; the `gh api markdown`
render when GitHub features are used; and what was not checked, such as
the final page or another renderer.

[gfm]: https://github.github.com/gfm/
[basic]: https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax
[headings]: references/headings-and-links.md#headings-as-the-outline
[anchors]: references/headings-and-links.md#section-links-and-heading-anchors
[toc]: references/headings-and-links.md#linked-contents-list
[custom]: references/headings-and-links.md#custom-anchors
[relative]: references/headings-and-links.md#relative-links
[refs]: references/headings-and-links.md#reference-style-links
[images]: references/headings-and-links.md#images-with-alt-text
[autolinks]: references/headings-and-links.md#autolinked-references
[fences]: references/blocks-and-lists.md#fenced-code-with-a-language
[nested]: references/blocks-and-lists.md#nested-fences
[tables]: references/blocks-and-lists.md#tables
[table-or-list]: references/blocks-and-lists.md#table-or-list
[lists]: references/blocks-and-lists.md#lists-and-nesting-indentation
[tasks]: references/blocks-and-lists.md#task-lists
[breaks]: references/blocks-and-lists.md#line-breaks
[escapes]: references/blocks-and-lists.md#backslash-escapes
[comments]: references/blocks-and-lists.md#html-comments
[renderers]: references/github-extensions.md#github-rendering-and-other-renderers
[alerts]: references/github-extensions.md#alerts
[footnotes]: references/github-extensions.md#footnotes
[details]: references/github-extensions.md#collapsed-sections
[mermaid]: references/github-extensions.md#mermaid-diagrams
[math]: references/github-extensions.md#math-expressions
[raw]: references/agent-readable-and-lint.md#raw-text-reads-without-rendering
[html]: references/agent-readable-and-lint.md#no-decorative-html
[lint]: references/agent-readable-and-lint.md#lint-rule-map
