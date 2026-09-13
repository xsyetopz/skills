---
name: maintain-agent-skills
description: >-
  Create, audit, merge, split, update, or validate Agent Skills packages and
  their metadata, instructions, scripts, references, and assets. Not for
  AGENTS.md.
---

# Maintain Agent Skills

For a collection audit, inventory every skill and bundled resource. For a
single-package change, inspect that package, its consumers, and neighboring
descriptions instead of loading the full catalog.

Read [specification and metadata](references/specification-and-metadata.md) for
the format and OpenAI integration. Read
[audit workflow](references/audit-workflow.md) for source research, progressive
disclosure, boundary changes, and verification.
Read [validation tool selection](references/validation-tools.md) before adding
or installing repository-wide validation tools.

When creating a package, start from the [SKILL.md
template](assets/SKILL.template.md). Replace its fields and keep only sections
with operational value. Do not create empty resource directories.

Keep one recognizable user goal per skill. Preserve useful depth while moving
conditional detail out of `SKILL.md`. Verify volatile technical claims against
the governing version and current authoritative upstream source. Validate
structure, metadata, links, scripts, examples, and observable workflow behavior.

Report boundary changes, obsolete guidance removed, source conflicts, and failed
or unavailable validation. Do not present a sample as a complete collection
audit.
