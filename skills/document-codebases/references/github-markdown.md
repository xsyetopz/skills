# GitHub Flavored Markdown

## Contents

- [Heading anchors](#heading-anchors)
- [Links](#links)
- [Contents lists](#contents-lists)
- [Code fences](#code-fences)
- [Tables](#tables)
- [Alerts](#alerts)
- [Collapsed sections](#collapsed-sections)
- [Mermaid, math, and footnotes](#mermaid-math-and-footnotes)
- [Lint](#lint)

## Heading anchors

GitHub builds an anchor from the heading text: lower-case, inline markup
removed, punctuation other than `-` and `_` removed, spaces to `-`.
A repeated anchor gets `-1`, `-2` in document order.

| Heading | Anchor |
| --- | --- |
| `## Options & flags` | `#options--flags` |
| `` ## `check_links.py` usage `` | `#check_linkspy-usage` |
| `## Setup` (second one) | `#setup-1` |

Models most often get the `&` case wrong (two hyphens, not one) and forget
that renaming a heading changes every link to it. After a rename run
`rg -n '#old-anchor'` and `scripts/check_links.py`.

Link only to a heading that exists; never invent an anchor.

## Links

- Link files in the repository with relative paths (`docs/setup.md`), not
  `github.com/.../blob/main/...` URLs. Relative links survive forks and
  branches, and they resolve from the file containing the link, not from
  the repository root.
- Link text says where the link goes. "here" and "this link" fail.
- Images need alt text that says what the image shows.
- For repeated or long URLs use reference definitions, and define every
  label you use.

## Contents lists

Add `## Contents` after the intro for files over about 100 lines or files
agents read in part. Each entry links to a heading anchor. Generate it
with `scripts/markdown_toc.py FILE.md` and verify with
`scripts/markdown_toc.py --check FILE.md`, because hand-written lists go
stale when headings change. Entries longer than the line limit become
reference links so markdownlint MD013 does not fail.

## Code fences

- Name a language on every fence; use `text` for plain output.
- To show a fence inside a fence, make the outer fence longer (four
  backticks around three).
- Put a blank line before and after a fence, and inside lists indent the
  fence to the item's content column.

## Tables

- Escape a pipe inside a cell as `\|`, even inside a code span.
- Every row needs the header's number of cells, and a blank line must
  precede the table or it renders as text.
- Use a table for lookup with short cells. Steps and long cells belong in
  a list.

## Alerts

```markdown
> [!NOTE]
> Text of the note.
```

The types are `NOTE`, `TIP`, `IMPORTANT`, `WARNING`, and `CAUTION`. The
marker must be alone on the first line of the quote, and a bold
`> **Note:**` is an ordinary quote, not an alert. Alerts do not render
inside lists or tables and show as plain quotes outside GitHub. Use one
only for something crucial, and never two in a row.

## Collapsed sections

```markdown
<details>
<summary>Full test log</summary>

Markdown here renders.

</details>
```

Keep the blank lines after `</summary>` and before `</details>`, or the
content shows as raw text. Do not hide required steps inside one.

## Mermaid, math, and footnotes

These render on GitHub only. Use a `mermaid` fence for diagrams, `$...$`
for math, and `[^1]` for footnotes. Render with `gh api markdown` in `gfm`
mode (uploads the text to GitHub; ask first for private content) to
check, because the default `markdown` mode does not render them.
When the page cannot be viewed, say so instead of claiming it renders.

## Lint

Use the repository's markdownlint configuration and do not relax a rule to
pass. MD051 checks anchors inside one file only; `scripts/check_links.py`
checks other files.
