# Agent-readable Markdown and lint

Agents read Markdown raw, often in part: the first lines, a heading
found with `grep`, or a line range. These cards keep the raw text as
clear as the rendered page, and map each rule in this skill to the
markdownlint rule that checks it. Rule names come from the markdownlint
0.41 rule documentation ([markdownlint rules][rules]).

## Contents

- [Raw text reads without rendering](#raw-text-reads-without-rendering)
- [Headings are the navigation](#headings-are-the-navigation)
- [No decorative HTML](#no-decorative-html)
- [Lint rule map](#lint-rule-map)

## Raw text reads without rendering

**Definition.** Every construct is chosen so the source file reads
correctly in a terminal: short lines, fenced code with a language, links
whose text says where they go, reference definitions at the end, and no
meaning carried only by color, icons, or layout.

**Use when.** Every Markdown file in a repository, and every issue or
pull request body an agent may fetch through an API.

**Do not use when.** Never skipped; the rendered page benefits from the
same choices.

**Example.** Raw text that reads well:

```markdown
Run `just markdown` before pushing; see [lint setup][lint].

[lint]: docs/lint.md
```

Raw text that does not: a 200-character line with two inline URLs, a
`<table>` of `<td>` cells, or a status shown only as an emoji.

**Cost removed.** Agents that misread wrapped HTML, miss a command inside
a table cell, or load a long file to find one section.

**Verify.** Read the file with `sed -n '1,40p' FILE`: the purpose, the
Contents list, and the first section are clear without a preview.

## Headings are the navigation

**Definition.** Headings are the only structure every tool sees: GitHub's
outline, `grep -n '^#'`, anchors, and an agent reading a line range.
Their text names the section's topic in words a reader would search for.

**Use when.** Naming and ordering sections in any file longer than one
screen.

**Do not use when.** A label inside a repeated structure (a card, a
definition list) would repeat the same heading many times; use bold run-in
labels there.

**Example.** `## Configure the proxy`, not `## Step 3` or `## Misc`. A
heading such as `## Notes` gives an agent no reason to read the section.

**Cost removed.** Agents reading whole files because no heading tells
them where the answer is.

**Verify.** `grep -nE '^#{2,3} ' FILE` alone tells a reader what the file
covers; no two sibling headings share text (MD024).

## No decorative HTML

**Definition.** Use HTML only where Markdown has no equivalent that
GitHub renders: `<details>`, `<a name>` anchors, `<sub>`, `<sup>`, `<br>`
in a table cell. Centered banners, `<p align="center">`, `<font>`,
spacer images, and `<table>` layouts are decoration.

**Use when.** Reviewing a README or template that wraps content in HTML.

**Do not use when.** A needed feature has no Markdown form; then keep the
HTML minimal. The secondary [Markdown Here cheatsheet][cheatsheet] notes
of Markdown inside HTML blocks: "Does *not* work **very** well."

**Example.**

```markdown
# ProjectName

Fast, local search for log files.
```

Not a `<div align="center">` block holding an `<img>` logo, an `<h1>`,
and a row of badges before the first sentence.

**Cost removed.** Tag noise before the first sentence, headings that are
not in the outline because they are HTML, and Markdown inside tags that
does not render.

**Verify.** `rg -n '<(div|p|center|font|table|h[1-6])\b' FILE` finds no
decorative tags. MD033 lists all inline HTML where the project enables it.

## Lint rule map

**Definition.** Most rules in this skill have a markdownlint rule that
checks them. Run the project's configured linter with the project's
config; do not add or relax rules to make a file pass.

**Use when.** Before finishing any Markdown change, and when a lint
message needs a fix.

**Do not use when.** The project has no Markdown linter; say so in the
report and check the rules by reading instead of adding a linter.

**Example.** Rules this skill relies on:

| Rule | Checks | Card |
| --- | --- | --- |
| MD001 | Heading levels increase by one | [Headings][headings] |
| MD003 | Heading style, such as ATX | [Headings][headings] |
| MD004 | Unordered list marker style | [Lists][lists] |
| MD007 | Unordered list indentation | [Lists][lists] |
| MD009 | Trailing spaces, including line breaks | [Line breaks][breaks] |
| MD013 | Line length, including code blocks when set | [Raw text][raw] |
| MD022 | Blank lines around headings | [Headings][headings] |
| MD024 | Headings with the same content | [Headings][headings] |
| MD025 | One top-level heading | [Headings][headings] |
| MD028 | Blank line inside a blockquote | [Alerts][alerts] |
| MD029 | Ordered list prefix | [Lists][lists] |
| MD031 | Blank lines around fenced code | [Fences][fences] |
| MD032 | Blank lines around lists | [Lists][lists] |
| MD033 | Inline HTML | [No decorative HTML][html] |
| MD034 | Bare URLs | [Autolinks][autolinks] |
| MD036 | Emphasis used instead of a heading | [Headings][headings] |
| MD040 | Fenced code has a language | [Fences][fences] |
| MD045 | Images have alt text | [Images][images] |
| MD046 | Code block style, such as fenced | [Fences][fences] |
| MD048 | Code fence character | [Nested fences][nested] |
| MD051 | Link fragments match a heading | [Anchors][anchors] |
| MD052 | Reference labels are defined | [Reference links][refs] |
| MD053 | Reference definitions are used | [Reference links][refs] |
| MD055 | Table pipe style | [Tables][tables] |
| MD056 | Table column count | [Tables][tables] |
| MD058 | Blank lines around tables | [Tables][tables] |
| MD059 | Link text is descriptive | [Raw text][raw] |

Lint does not check that a Contents list matches the headings
(`markdown_toc.py --check` does), that an alert type is valid, that a
link to another file resolves, or that GitHub-only features render
elsewhere.

**Cost removed.** Style arguments in review, and fixes that silence a
rule instead of meeting it.

**Verify.** The project's own command passes, such as `just markdown` or
a `markdownlint-cli2` run with the repository's config file. Report the
command and its result; if none exists, say so.

[alerts]: github-extensions.md#alerts
[anchors]: headings-and-links.md#section-links-and-heading-anchors
[autolinks]: headings-and-links.md#autolinked-references
[breaks]: blocks-and-lists.md#line-breaks
[cheatsheet]: https://github.com/adam-p/markdown-here/wiki/markdown-cheatsheet
[fences]: blocks-and-lists.md#fenced-code-with-a-language
[headings]: headings-and-links.md#headings-as-the-outline
[html]: #no-decorative-html
[images]: headings-and-links.md#images-with-alt-text
[lists]: blocks-and-lists.md#lists-and-nesting-indentation
[nested]: blocks-and-lists.md#nested-fences
[raw]: #raw-text-reads-without-rendering
[refs]: headings-and-links.md#reference-style-links
[rules]: https://github.com/DavidAnson/markdownlint/blob/main/doc/Rules.md
[tables]: blocks-and-lists.md#tables
