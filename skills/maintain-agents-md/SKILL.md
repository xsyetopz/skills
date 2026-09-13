---
name: maintain-agents-md
description: >-
  Create or audit scoped AGENTS.md instructions from repository evidence and
  directory precedence. Not for Agent Skills or general documentation.
---

# Maintain AGENTS.md

1. Read the applicable instruction chain, manifests, CI commands, scripts, and
   code for the requested directory scope.
1. Resolve contradictory or stale instructions against their sources and
   explicit user requirements.
1. Put shared instructions at the repository root. Put subtree-specific
   differences in the nearest applicable nested file.
1. Write direct instructions for consequential commands, ownership boundaries,
   and constraints. Include command working directories and prerequisites.
1. Check paths, links, command definitions, precedence, and the consumer's size
   limit. Report execution results only for checks actually run.

Use plain Markdown. AGENTS.md has no required schema or heading set. Do not
invent one or copy generic coding advice into each scope.

Read [discovery and evidence][ref-1] when checking discovery or precedence,
resolving conflicting guidance, or choosing root versus nested placement. Its
Codex overrides and fallback names are client-specific. GitHub
`.github/agents/*.agent.md` personas use a different format.

[ref-1]: references/format-and-evidence.md
