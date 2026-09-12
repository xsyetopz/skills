---
name: create-red-green-examples
description: >-
  Construct compact paired RED (wrong) and GREEN (correct) implementation
  examples with an explicit deciding condition and meaningful checks. Use when
  the user asks for wrong/right code comparisons, not test-driven-development
  red/green cycles or ordinary implementation.
---

# Create RED/GREEN Examples

RED and GREEN here are contrastive examples, not test-driven-development
states. RED always means an implementation to avoid for the stated condition.
GREEN always means the smallest implementation that satisfies that condition.

State the deciding condition literally before the pair. Keep the same domain,
language, inputs, surrounding context, and goal in both examples. Change only
what establishes the decision. DO NOT compare an unrelated toy RED with a
framework-heavy GREEN, or use tone to imply the rule.

For each pair, provide this structure:

1. `### RED — DO NOT: <specific failure>` with valid code unless syntax is the
   lesson; explain the violated invariant and consequence.
2. `### GREEN — DO: <correct behavior>` with the corresponding correction;
   explain why it is sufficient, not merely more elaborate.
3. `Check:` with an exact command, assertion, or inspection that distinguishes
   the pair. Run implementation-oriented checks in an isolated workspace when
   practical. A RED check must demonstrate its intended defect; a GREEN check
   must demonstrate the stated contract.

Use a direct call, platform facility, standard format, or single module when it
meets the stated condition. Add an interface, event, schema version, custom
protocol, registry, service layer, or compatibility path only after naming the
current boundary or requirement that requires it.

Read [pair construction examples](references/pair-construction.md) for a
reusable format and examples covering unnecessary abstraction, standard formats,
and incomplete reproductions.
