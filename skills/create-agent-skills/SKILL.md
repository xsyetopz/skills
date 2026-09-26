---
name: create-agent-skills
description: >-
  Creates, rewrites, and audits Agent Skills (SKILL.md) for Claude Code and
  Codex: descriptions, progressive disclosure, scripts, evals, and
  agents/openai.yaml. Use when writing or improving a skill. Not for AGENTS.md
  or for doing the task a skill describes.
---

# Create Agent Skills

Build skills that give an agent what it lacks and leave it nothing to
invent. A skill is a directory whose `SKILL.md` routes observed evidence to
cards in `references/`. A card covers one construct that agents get wrong
without the skill: a definition, when to use it and when not to, a complete
working example, the cost it removes and how to observe that, and exact
verification steps. Runnable examples and helper scripts prove the claims.

## Workflow

1. Collect evidence before writing: real task prompts, the target hosts and
   versions, primary documentation for the domain, and failures agents
   make without the skill. Write `evals/evals.json` first
   ([evaluation](references/evaluation.md#evalsjson)).
1. List the constructs an expert would check for this task that agents
   get wrong without help
   ([choosing constructs](references/construct-cards.md#choosing-constructs)).
   Give each variant its own card.
1. For each construct, write the runnable example in `assets/examples/`
   first (baseline and candidate where the card transforms code), with an
   oracle and a benefit assertion
   ([executable resources](references/executable-resources.md)).
1. Write the cards from
   [`assets/card.template.md`](assets/card.template.md); every number cites
   a source or a labeled local run; every example states its verification
   tier ([grounding](references/construct-cards.md#grounding-and-numbers)).
1. Write `SKILL.md` from
   [`assets/SKILL.template.md`](assets/SKILL.template.md): workflow with
   exact commands, a routing table from observed evidence to card anchors,
   rules for known failures, bundled tools, references, completion
   evidence. Keep the body within the host's and repository's limits
   ([disclosure budget][budget]).
1. Write the description last, from the evals
   ([descriptions](references/descriptions.md)): third person, what the
   skill does and then when to use it, key use case first. Claude Code cuts
   each listing entry at 1,536 characters and budgets the whole listing at
   1% of the context window; Codex budgets 2% of the context window, or
   8,000 characters when the window is unknown. Then write `agents/openai.yaml`
   for Codex ([Codex metadata](references/codex-metadata.md)).
1. Validate: `skills-ref validate <dir>`, then
   `python3 scripts/check_reference_structure.py <dir>`, then the
   repository's Markdown, script, and asset checks, then every example
   verifier.
1. Run the evals on the target hosts with and without the skill
   ([paired protocol](references/evaluation.md#paired-evaluation-protocol))
   or state that trials were not run.

For an existing skill, start with
[audit and rewrite](references/audit-and-rewrite.md): detect templated
text, find thin constructs, salvage real content, then follow the workflow.

## Route the task to a card

| Task or symptom | Card |
| --- | --- |
| Starting a new skill directory | [Directory layout](references/package-format.md#directory-layout) |
| Frontmatter fields and limits | [Frontmatter](references/package-format.md#skillmd-frontmatter) |
| Choosing or changing a name | [Name](references/package-format.md#name) |
| Deciding what goes in body versus references | [Disclosure budget](references/package-format.md#progressive-disclosure-budget) |
| Agent misses content in references | [One level deep](references/package-format.md#references-one-level-deep) |
| Deciding between a script and instructions | [Scripts](references/package-format.md#scripts-execute-or-read), [Helper script](references/executable-resources.md#deterministic-helper-script) |
| Claude Code-only fields, manual-only skills | [Claude Code extensions](references/package-format.md#claude-code-frontmatter-extensions) |
| Install paths and invocation per host | [Discovery](references/package-format.md#host-discovery-and-invocation) |
| Skill does not trigger, or triggers wrongly | [Description structure](references/descriptions.md#description-structure), [Triggering evaluation](references/descriptions.md#triggering-evaluation) |
| Many skills, descriptions truncated | [Length budget](references/descriptions.md#length-budget-across-a-catalog) |
| Writing a card | [Card structure](references/construct-cards.md#card-structure) |
| Examples that might not compile | [Examples that run](references/construct-cards.md#examples-that-run) |
| Claims without evidence | [Cost removed](references/construct-cards.md#cost-removed-and-measurement), [Grounding](references/construct-cards.md#grounding-and-numbers) |
| Examples that need unavailable tools | [Verification tiers](references/construct-cards.md#verification-tiers), [SKIP vs FAIL](references/executable-resources.md#skip-versus-fail) |
| Requirements, plans, reviews, other text artifacts | [Non-code skills](references/construct-cards.md#non-code-skills) |
| Build output leaking into the skill | [Disposable-copy verifier](references/executable-resources.md#disposable-copy-verifier) |
| Proving a transformation is safe and useful | [Oracle](references/executable-resources.md#equivalence-oracle-with-a-benefit-assertion) |
| Batch or destructive operations | [Plan-validate-execute](references/executable-resources.md#plan-validate-execute) |
| Codex UI, implicit invocation, MCP servers | [Codex metadata](references/codex-metadata.md) |
| Writing evals and assertions | [evals.json](references/evaluation.md#evalsjson), [Assertions](references/evaluation.md#assertions-that-can-be-checked) |
| A revision did not help | [Failure classification](references/evaluation.md#failure-classification) |
| Is the skill complete? | [Content sufficiency](references/evaluation.md#content-sufficiency-test) |
| Existing skill is generic or repetitive | [Templated boilerplate](references/audit-and-rewrite.md#templated-boilerplate), [Thin cards](references/audit-and-rewrite.md#thin-card-detection) |

## Rules

- Give every construct that agents get wrong a full card: definition, use
  when, do not use when, working example, cost removed with its
  instrument, verify steps. A bullet or a sentence is not a card.
- No invented API names, flags, defaults, version boundaries, or numbers.
  Cite primary sources; label local measurements with command, machine,
  and toolchain; mark anything unexecuted as such.
- Report measurements that show no benefit; they stop agents from making
  useless changes.
- Link every reference directly from `SKILL.md`, because agents may only
  preview a file reached through another reference; give references over
  100 lines a `## Contents` section so a partial read still shows the scope.
- Runnable assets build and run in a disposable copy; no build output in
  the skill directory.
- Do not rename a published skill; renames break invocations.
- Published skills must not link to internal maintenance records.
- Static validation does not show that a skill changes agent behavior;
  report evaluation trials separately, or say they were not run.

## Bundled tools

- `scripts/check_reference_structure.py SKILL_DIR...`: checks that every
  reference is linked from `SKILL.md`, long references have contents,
  relative links and anchors resolve, and name and description are valid;
  exit 0 clean, 1 problems, 2 bad input.
- `assets/SKILL.template.md` and `assets/card.template.md`: starting
  points for the entry file and for each card.

## References

- [Package format](references/package-format.md): layout, frontmatter,
  names, disclosure budget, references, scripts, assets, host discovery,
  Claude Code extensions.
- [Descriptions](references/descriptions.md): structure, trigger words,
  boundary clause, catalog budget, triggering evaluation.
- [Construct cards](references/construct-cards.md): card structure,
  choosing constructs, variants, runnable examples, cost and measurement,
  verification tiers, grounding, non-code skills.
- [Executable resources](references/executable-resources.md): helper
  scripts, exit codes, disposable-copy verifiers, oracles, SKIP versus
  FAIL, plan-validate-execute.
- [Evaluation](references/evaluation.md): evals.json, assertions, paired
  protocol, failure classification, content sufficiency.
- [Audit and rewrite](references/audit-and-rewrite.md): boilerplate and
  thin-card detection, salvage, patterns not to copy, coverage records.
- [Codex metadata](references/codex-metadata.md): interface fields,
  invocation policy, MCP dependencies, loader behavior.

## Completion evidence

The report lists: the evals written; the constructs and their cards; each
example's verification tier with the command and result; validator output
(`skills-ref`, the structure checker, repository checks); description
length; and whether host trials ran, with results, or were not run.

[budget]: references/package-format.md#progressive-disclosure-budget
