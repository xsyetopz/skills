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

Read [specification and metadata](references/specification-and-metadata.md) when
creating a package or checking format, discovery, client metadata, or authoring
sources. Read [audit workflow](references/audit-workflow.md) for collection
audits, boundary changes, or behavioral evaluation.
Read [validation tool selection](references/validation-tools.md) before adding
or installing repository-wide validation tools.

When creating a package, start from the [SKILL.md
template](assets/SKILL.template.md). Replace its fields and keep only sections
with operational value. Do not create empty resource directories.

Keep one recognizable user goal per skill. Put its outcome and essential
constraints first. Give each action a concrete verb, target, and condition;
name the artifact or result that completes it. Explain terms needed to choose
the next action. Give every reference an explicit loading condition.
Simple skills can remain self-contained. Preserve useful depth, not generic
advice, duplicated rules or mandatory steps unrelated to the requested outcome.
Use exact procedures where variation threatens correctness or preservation;
otherwise give one practical default and the conditions for exceptions.

Optimize useful specificity per word, not minimum length. Preserve inputs,
decision criteria, ordered procedures, exceptions, examples, failure handling,
and completion evidence when compressing; remove repeated or vague wording.
Respect the consuming repository's size limits and counting rules through its
existing validation. Keep conditional depth in references; do not invent a
numerical ceiling or treat line count as a measure of instruction quality.

Before repairing a failure, define a realistic scenario and an observable result
that distinguishes the intended behavior from a plausible shortcut. Separate
selection, context loading, understanding, application and completion-claim
failures. Verify changed technical claims against authoritative version-matched
sources. Run relevant package checks and distinguish structural validation,
manual scenario review, executed mechanics and actual agent evaluations.

Report changes, source conflicts, and failed or unavailable checks. For a
collection audit, mark every package as changed, reviewed without changes,
or unresolved; record why each resource is retained, merged, or removed. Do not
present a sample as a complete collection audit.
