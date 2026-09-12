---
name: maintain-repository-docs
description: >-
  Write or audit README, CONTRIBUTING, guides, and other repository
  documentation using executable project evidence. Use when repository
  documentation content is the requested outcome; not for AGENTS.md,
  changelogs, hosted templates, CODEOWNERS, or runtime implementation.
---

# Maintain Repository Docs

Apply this workflow when repository documentation is the requested work, not
merely because another task includes necessary documentation. Implicit
activation does not authorize unrelated implementation changes.

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
