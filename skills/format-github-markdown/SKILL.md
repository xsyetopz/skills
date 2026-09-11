---
name: format-github-markdown
description: >-
  Explicitly format, normalize, or lint GitHub Flavored Markdown with the
  bundled markdownlint-cli2 policy. Activate only when invoked as
  $format-github-markdown; excludes deciding document content or repository
  governance.
---

# Format GitHub Markdown

Run this workflow only when the user explicitly invokes this skill by name.
A mention of Markdown in another task is not an invocation.

Preserve content, links, code semantics, and repository conventions. Use the
repository's configured formatter and lint command first. Do not replace its
policy with this skill's preferences or disable diagnostics to obtain success.

## Configuration and execution

Inspect the configured command as well as files: it may select a custom
configuration with `--config` or `--configPointer`. CLI2 discovers
`.markdownlint-cli2.jsonc`, `.yaml`, `.cjs`, and `.mjs`, but not
`.markdownlint-cli2.json`. It also reads the documented `.markdownlint.*`
rule configurations. See [upstream configuration][configuration].

Only when adding tooling is in scope and no configuration already governs the
target, use `scripts/ensure-markdownlint-cli2.sh <repo-root>`. It preserves
recognized root configuration files and installs
`assets/.markdownlint-cli2.jsonc` otherwise. It does not inspect custom command
arguments or replace nested configurations. Review those before running it.

The fallback runner `scripts/lint-markdown.sh` invokes pinned CLI2 through
`bunx`; it is not a reason to replace an existing project command or version.
Run from the intended project root and quote globs. For a standalone project:

```sh
scripts/lint-markdown.sh --fix '**/*.md'
scripts/lint-markdown.sh '**/*.md'
```

Narrow the glob to the requested files. The final non-fixing invocation must
succeed. Auto-fix alone is not verification, and it does not generally reflow
paragraphs. Fix residual diagnostics without changing literal URLs, hashes,
identifiers, or command behavior.

## Bundled policy

The asset favors ATX headings, dash lists, backtick fences, and compact tables.
Its MD013 policy limits prose to 80 columns but excludes fenced code and tables;
a project's own configuration can impose different limits. The asset is the
rule source, not a claim that these preferences are required by GFM.

Let the configured formatter own whitespace. If it conflicts with a configured
lint rule, resolve the tool/policy conflict with the user instead of alternating
formatters forever. For relationships or flows, prefer Mermaid; use prose or a
list when simpler. Never add a diagram merely to fill a template.

[configuration]: https://github.com/DavidAnson/markdownlint-cli2#configuration
