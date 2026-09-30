# Blocks and lists

Code blocks, tables, lists, line breaks, escapes, and comments: the block
syntax that breaks most often when written from memory. Quotes come from
the [GFM spec][spec] (version 0.29-gfm) and GitHub Docs pages
[Basic writing and formatting syntax][basic],
[Creating and highlighting code blocks][code], and
[Organizing information with tables][tables].

## Contents

- [Fenced code with a language](#fenced-code-with-a-language)
- [Nested fences](#nested-fences)
- [Tables](#tables)
- [Table or list](#table-or-list)
- [Lists and nesting indentation](#lists-and-nesting-indentation)
- [Task lists](#task-lists)
- [Line breaks](#line-breaks)
- [Backslash escapes](#backslash-escapes)
- [HTML comments](#html-comments)

## Fenced code with a language

**Definition.** A fence is "a sequence of at least three consecutive
backtick characters (`) or tildes (~)". Text after the opening fence is
the info string; "The first word of the info string is typically used to
specify the language of the code sample". GitHub uses it for syntax
highlighting and selects grammars with Linguist.

**Use when.** Every block of code, commands, output, configuration, or
file content. Use `text` for output or prose that has no language.

**Do not use when.** The code is a short name or command inside a
sentence; use an inline code span (`` `git status` ``).

**Example.**

````markdown
```sh
bun install --frozen-lockfile
```

```text
Checked 12 packages, 0 changed.
```
````

GitHub recommends "placing a blank line before and after code blocks to
make the raw formatting easier to read." For GitHub Pages, "use
lower-case language identifiers."

**Cost removed.** Unhighlighted blocks, and agents guessing whether a
block is a command to run, output to compare, or a file to write.

**Verify.** markdownlint MD040 (language present), MD031 (blank lines
around fences), and MD046 (fenced style) pass.

## Nested fences

**Definition.** A fenced block ends only at "a closing code fence of the
same type as the code block began with (backticks or tildes), and with
at least as many backticks or tildes as the opening code fence." An outer
fence that is longer than, or of a different character from, any inner
fence contains it.

**Use when.** Showing Markdown that itself holds a fenced block: a README
sample, a skill template, a card example.

**Do not use when.** The inner content has no fence; extra backticks only
add noise.

**Example.** Four backticks around a three-backtick block:

`````markdown
````markdown
Run the tests:

```sh
just tests
```
````
`````

A tilde fence (`~~~markdown`) around backtick fences also works, but
check the project's fence style first; markdownlint MD048 set to
`backtick` rejects tildes.

**Cost removed.** An inner closing fence that ends the outer block early,
so the rest of the file renders as code or loses its code.

**Verify.** View the rendered file, or lint it: prose rules firing inside
what should be code, or MD040 on a fence you meant as content, shows the
outer block closed early.

## Tables

**Definition.** A GFM table is "a single header row, a delimiter row
separating the header from the data, and zero or more data rows." Colons
in the delimiter row align columns: left `:---`, center `:---:`, right
`---:`. "The header row must match the delimiter row in the number of
cells. If not, a table will not be recognized". GitHub: "You must include
a blank line before your table in order for it to correctly render."

**Use when.** Records with the same two to five short fields each:
options with defaults, a routing table, a comparison.

**Do not use when.** Cells need paragraphs, lists, or code blocks:
"Block-level elements cannot be inserted in a table." Use a
[list](#table-or-list) instead.

**Example.** A pipe inside a cell, even inside a code span, is escaped as
`\|`; the spec: "Include a pipe in a cell's content by escaping it,
including inside other inline spans".

```markdown
| Operator | Meaning |
| --- | --- |
| `a \|\| b` | Logical or |
| `\|` | Pipe to the next command |
```

"The table is broken at the first empty line, or beginning of another
block-level structure", so keep rows contiguous. Use leading and trailing
pipes; the spec recommends them "for clarity of reading".

**Cost removed.** A row split into extra columns by a stray `|`, and a
table that renders as one paragraph because the delimiter row is short.

**Verify.** markdownlint MD055 (pipe style), MD056 (column count), and
MD058 (blank lines around tables) pass. Count cells in the header and
delimiter rows.

## Table or list

**Definition.** A table compares records along the same fields; a list
gives items that each need their own sentence or structure.

**Use when.** Use a list when any cell would exceed about one line, when
rows have different fields, or when a cell needs a code block.

**Do not use when.** Records share the same short fields and a reader
scans down a column; then a table is easier to compare.

**Example.**

```markdown
- `--check`: exits 1 when a Contents list is stale; use it in CI.
- `--max-level N`: includes headings down to level N (default 2).
```

**Cost removed.** Wide raw tables that wrap into unreadable rows, which
agents parse cell by cell.

**Verify.** Each table row fits on a screen in the raw file, and no cell
holds `<br>` or a list.

## Lists and nesting indentation

**Definition.** Unordered items start with `-`, `*`, or `+`; ordered items
with a number and `.`. Nested content belongs to an item when indented to
its content: "the position of the text after the list marker determines
how much indentation is needed in subsequent blocks in the list item."
GitHub's example: under `100. First list item`, a nested item needs "a
minimum of five spaces".

**Use when.** Steps (ordered), sets of parallel items (unordered), and
code blocks or paragraphs that belong to one step (indented under it).

**Do not use when.** The items are one sentence of prose; a list of one
item, or a list used for layout, adds structure without meaning.

**Example.**

````markdown
1. Install the tools:

   ```sh
   bun install
   ```

1. Run the checks.
   - `just markdown` for Markdown only.
````

Indent by the marker width: 2 spaces under `-`, 3 under `1.`. Check the
project's list rules first; a project may require `1.` for every ordered
item (MD029 `one`) or a fixed indent (MD007).

**Cost removed.** A code block that falls out of its step and restarts the
numbering, or a nested item rendered as a sibling.

**Verify.** markdownlint MD004, MD005, MD007, MD029, MD030, and MD032
pass; in the rendered view, the code block sits inside its step.

## Task lists

**Definition.** A list item that starts with `[ ]` or `[x]` renders as a
checkbox. GitHub: "preface list items with a hyphen and space followed by
`[ ]`. To mark a task as complete, use `[x]`."

**Use when.** Checklists in issues, pull request descriptions, and
release or review steps in repository files.

**Do not use when.** The items are not tasks with a done state. If an
item starts with a parenthesis, escape it: "If a task list item
description begins with a parenthesis, you'll need to escape it with `\`".

**Example.**

```markdown
- [x] Update the changelog
- [ ] Tag the release
- [ ] \(Optional) Announce it
```

**Cost removed.** Checkbox text that renders as a literal `[ ]` because
the marker is missing its space or list dash.

**Verify.** Each task line matches `^\s*- \[[ xX]\]` and a space.

## Line breaks

**Definition.** In a `.md` file a single newline does not break the line.
A hard break is a line ending preceded by a backslash or by two or more
spaces; the spec calls the backslash "a more visible alternative".
GitHub also accepts `<br/>`. In issues, pull requests, and discussions,
GitHub renders a plain newline as a break.

**Use when.** An address, a poem, or a label and value that must stay on
separate lines inside one paragraph.

**Do not use when.** A blank line (a new paragraph) or a list says the
same thing. Never use trailing spaces: they are invisible in the raw file
and removed by editors; markdownlint MD009 with `br_spaces: 0` rejects
them.

**Example.**

```markdown
Octo Corp\
1 Main Street
```

**Cost removed.** Breaks that disappear when an editor strips trailing
whitespace.

**Verify.** `rg -n ' +$' FILE` prints nothing; MD009 passes.

## Backslash escapes

**Definition.** "Any ASCII punctuation character may be
backslash-escaped", and "Escaped characters are treated as regular
characters and do not have their usual Markdown meanings". A backslash
before any other
character stays literal. GitHub: "The Markdown formatting will not be
ignored in the title of an issue or a pull request."

**Use when.** A literal `*`, `_`, `#`, `[`, `|`, or `<` in prose would
otherwise start formatting, a heading, a link, or a table cell.

**Do not use when.** The text is code, a path, or a command; put it in a
code span, which is not parsed and reads cleanly raw.

**Example.**

```markdown
Rename \*draft\* to *final*. Use `*.md` to match every file.
```

**Cost removed.** Stray italics and broken tables from punctuation in
prose.

**Verify.** Rendered output shows the literal characters; the raw text
still reads without the backslashes being distracting (if it does not,
switch to a code span).

## HTML comments

**Definition.** "You can tell GitHub to hide content from the rendered
Markdown by placing the content in an HTML comment." The text stays in
the raw file.

**Use when.** Lint suppressions (`<!-- markdownlint-disable-next-line
MD013 -->`), notes to maintainers or tools, and markers that generators
look for.

**Do not use when.** The content is secret, or is guidance agents must
follow; agents read raw files, so hidden text is not hidden from them,
and human readers never see it.

**Example.**

```markdown
<!-- Generated by tools/gen_api.py; edit the source, not this table. -->
```

**Cost removed.** Maintainer notes that leak into the rendered page.

**Verify.** `rg -n '<!--' FILE` lists every comment; each one is still
true and needed.

[basic]: https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax
[code]: https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/creating-and-highlighting-code-blocks
[spec]: https://github.github.com/gfm/
[tables]: https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/organizing-information-with-tables
