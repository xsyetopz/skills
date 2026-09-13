---
name: maintain-repository-docs
description: >-
  Write or audit README, CONTRIBUTING, guides, and repository documentation from
  executable project evidence. Not for AGENTS.md or changelogs.
---

# Maintain Repository Docs

Identify the reader's task. Derive claims from manifests, source, CI, scripts,
and observed commands. For README or CONTRIBUTING work, read
[README and contribution guidance](references/readme-and-contributing.md). For
tutorials, API references, architecture decisions, diagrams, or executable
examples, read [structure and checks](references/structure-and-validation.md).

Preserve the requested document’s purpose rather than imposing a universal
outline. Verify changed links, paths, prerequisites, commands, expected results,
and platform claims. Run changed examples from their documented directory when
they can be tested without deployment or publication. Report commands and
observed results separately from unexecuted procedures and unresolved facts.

Use the bundled [README](assets/README.template.md) or
[CONTRIBUTING](assets/CONTRIBUTING.template.md) template only when its sections
match the repository. Remove unused optional sections rather than leaving
placeholders or empty headings.
