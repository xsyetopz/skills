# render

render turns a Markdown file into HTML and writes it next to the input file, keeping the same base name and replacing the extension with .html.

## Flags

| Flag | Meaning |
| --- | --- |
| `--out DIR` | Write the HTML into DIR instead |
| `--format html|text` | Output format |

> **Note:**
> The input file is never modified.

<details>
<summary>Example log</summary>
```text
rendered docs/intro.md -> docs/intro.html
```
</details>
