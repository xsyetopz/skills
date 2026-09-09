---
name: agents-md-creator
description:
  Create or audit AGENTS.md instructions from repository evidence and directory
  scope. Excludes GitHub custom-agent personas and general project
  documentation.
---

# AGENTS.md Creator

1. Read the applicable instruction chain, manifests, CI commands, scripts, and
   code for the requested directory scope.
2. Resolve contradictory or stale instructions against their sources and
   explicit user requirements.
3. Put shared instructions at the repository root. Put subtree-specific
   differences in the nearest applicable nested file.
4. Write direct instructions for consequential commands, ownership boundaries,
   and constraints. Include command working directories and prerequisites.
5. Check paths, links, command definitions, precedence, and the consumer's size
   limit. Report execution results only for checks actually run.

Use plain Markdown. AGENTS.md has no required schema or heading set. Do not
invent one or copy generic coding advice into each scope.

Read [discovery and evidence][ref-1] for Codex overrides, fallback names,
root/nested examples, and conflicting guidance. GitHub
`.github/agents/*.agent.md` personas use a different format.

[ref-1]: references/format-and-evidence.md
