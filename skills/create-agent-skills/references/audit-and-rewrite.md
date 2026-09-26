# Audit and rewrite

Finding thin or templated content in existing skills and rebuilding it
as construct cards without losing what was real.

## Contents

- Templated boilerplate
- Thin card detection
- Salvage before delete
- Patterns not to copy
- Catalog coverage record

## Templated boilerplate

**Definition.** Text repeated across many skills with only the topic
noun swapped, giving an agent no domain knowledge: generic operating
contracts, model-version paragraphs, "follow best practices", and
reference files named after abstract categories (concepts and
invariants, organizational controls, resource maps) instead of
constructs.

**Use when.** Auditing a catalog or a skill you did not write.

**Do not use when.** The repeated text is a deliberate shared rule (the
same validation command in every skill); keep it short and specific.

**Example.** Detect paragraphs shared by many skills:

```sh
for f in skills/*/SKILL.md; do
  awk 'BEGIN{RS=""} {gsub(/\n/," "); print}' "$f"
done | sort | uniq -c | sort -rn | awk '$1 > 5' | head
```

A paragraph in more than a handful of skills is a candidate for
deletion or for replacement with domain content.

**Cost removed.** Context spent on text that changes no decision.

**Verify.**

1. After the rewrite, the same command shows the repeated paragraphs
   gone or reduced to intentional shared rules.

## Thin card detection

**Definition.** A thin construct appears only as a bullet, table cell,
or sentence, lacking a definition, conditions, a working example, a
measurable cost, or verification steps.

**Use when.** Reviewing references for completeness.

**Do not use when.** The item is supporting context, not a construct an
agent applies.

**Example.** Thin: "use spans/pooling only with lifetime measurements."
Complete: the "Bounded stackalloc with ArrayPool fallback" card in
`optimize-csharp-code`, with the bound, the failure mode
(`StackOverflowException`), the runnable method, and the oracle.

**Cost removed.** Agents implementing a construct from a one-line hint.

**Verify.**

1. Each construct the skill mentions (`rg -n '^- ' references/`) has
   its own card or is supporting context.

## Salvage before delete

**Definition.** Before deleting old content, move every verified fact,
source link, semantic trap, and working example into the new cards, then
delete the old files in the same change.

**Use when.** Replacing any existing reference or asset.

**Do not use when.** Never keep old and new side by side "for
reference"; duplicated, divergent guidance is worse than either.

**Example.** An old reference said "`Enum.HasFlag(mask)` has all-bits
semantics, true for a zero mask; `(value & mask) != 0` is not equivalent."
That became the "Enum.HasFlag semantics" card with an oracle over every
value and mask pair.

**Cost removed.** Losing hard-won facts in a rewrite.

**Verify.**

1. `git diff --stat` shows the old files deleted and new ones added in one
   change.
1. For each deleted file, name the card that now holds its real content,
   or state that it had none.

## Patterns not to copy

**Definition.** Features of popular skill repositories that are not
requirements.

**Use when.** Borrowing structure from another collection.

**Do not use when.** The feature serves a real need in your package.

**Example.** Do not copy: optional host metadata (icons, colors, MCP
dependencies) the package does not need; a fixed reviewer count or phase
model; a terse public skill's length as evidence that little content is
needed (it may rely on private tools); a huge reference dump that
SKILL.md does not route into.

**Cost removed.** Cargo-culted structure that adds maintenance without
changing behavior.

**Verify.**

1. Each non-required file or field has a stated reason in the change
   description.

## Catalog coverage record

**Definition.** For a catalog-wide rewrite, one record per skill: its
status (changed, reviewed without changes, or unresolved), the deciding
evidence, and any validation that could not run. Keep it outside the
published packages, for example in `docs/audits/`.

**Use when.** Rewriting or auditing many skills at once.

**Do not use when.** Never link to it from a published skill; published
instructions must not depend on internal maintenance records.

**Example.**

```text
optimize-csharp-code  changed  39 cards; verify.sh verify 99 checks pass;
                               NativeAOT link not runnable (MSB3073)
write-justfiles       changed  ...
```

**Cost removed.** Skills silently skipped in a catalog pass.

**Verify.**

1. The record lists every directory under `skills/`
   (`ls skills | wc -l` equals the record's row count).
