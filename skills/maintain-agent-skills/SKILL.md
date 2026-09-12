---
name: maintain-agent-skills
description: >-
  Use only when explicitly invoked by name. Create, audit, update, split, merge,
  or validate Agent Skills packages from current specifications and
  authoritative domain sources. Excludes AGENTS.md, general repository
  documentation, and unrelated product implementation.
---

# Maintain Agent Skills

Run this workflow only when the user explicitly invokes this skill by name. A
related keyword or an ordinary implementation request is not an invocation.

Inventory every skill and its `SKILL.md`, `agents/`, `references/`, `assets/`,
scripts, examples, tests, and cross-skill references. Determine each workflow's
user goal, inputs, outputs, success condition, exclusions, and related skills
before changing its name or boundary.

Read [specification and metadata](references/specification-and-metadata.md) for
the format and OpenAI integration. Read
[audit workflow](references/audit-workflow.md) for source research, progressive
disclosure, boundary changes, and verification.
Read [validation tool selection](references/validation-tools.md) before adding
or installing repository-wide validation tools.

When creating a package, start from the [canonical SKILL.md
template](assets/SKILL.template.md). Replace its required fields and keep only
sections with operational value. Do not create empty resource directories.

Keep one recognizable user goal per skill. Preserve useful depth while moving
conditional detail out of `SKILL.md`. Verify volatile technical claims against
the governing version and current authoritative upstream source. Validate
structure, metadata, links, scripts, examples, and observable workflow behavior.

Report boundary changes, material knowledge updates, obsolete guidance removed,
source conflicts, and failed or unavailable validation. Do not present an
inventory sample as a complete collection audit.
