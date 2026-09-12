---
name: maintain-repository-docs
description: >-
  Use only when explicitly invoked by name. Write or audit README, CONTRIBUTING,
  and other repository documentation from executable project evidence. Excludes
  AGENTS.md, changelogs, hosted templates, CODEOWNERS, and runtime
  implementation.
---

# Maintain Repository Docs

Run this workflow only when the user explicitly invokes this skill by name. A
related keyword or an ordinary implementation request is not an invocation.

Derive claims from manifests, source, CI, scripts, and observed commands. Read
[README and contribution guidance](references/readme-and-contributing.md). For
tutorials, API references, ADRs, diagrams, or executable examples, read
[structure and validation](references/structure-and-validation.md).

Preserve the requested document’s purpose rather than imposing a universal
outline. Verify changed links, paths, prerequisites, commands, expected results,
and platform claims. Report unresolved factual decisions instead of inventing
them.

Use the bundled [general Markdown](assets/MARKDOWN.template.md),
[README](assets/README.template.md), or
[CONTRIBUTING](assets/CONTRIBUTING.template.md) template only when its sections
match the repository. Remove unused optional sections rather than leaving
placeholders or empty headings.
