# GitHub Flavored Markdown

Preserve the source meaning. Use heading levels as a hierarchy, not as visual
font sizes. Use a fenced code block with an appropriate language tag for
commands or source; choose a longer outer fence when demonstrating nested
fences. Keep filenames and identifiers in inline code.

Use tables for genuinely tabular comparisons, not multiline procedures or code.
Escape literal pipes in table cells when needed. Check relative links from the
document's actual location and rendered anchors for headings with punctuation or
repeated names. Prefer repository-relative links when they should follow the
branch.

Use task lists only for actual checkable work; do not convert descriptive lists
into implied pending tasks. Use alerts or `<details>` only when the target
supports them and they improve navigation. Do not rely on arbitrary HTML, CSS,
or JavaScript in GitHub rendering.

A formatter or linter can validate selected syntax/style rules, not factual
correctness or full rendered behavior. Inspect the target rendering when layout
is part of the requested result. Do not change code, command flags, URLs, or
line-sensitive examples merely to satisfy a prose wrap width.

Sources: [GFM specification](https://github.github.com/gfm/), [GitHub basic
writing syntax][ref-github-basic-writing-syntax].

[ref-github-basic-writing-syntax]: https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax
