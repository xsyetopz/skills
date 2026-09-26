# Evaluation

Static checks prove a package is well-formed; only runs on the target
host prove it changes agent behavior. These cards cover the eval file,
the paired protocol, and failure classification.

## Contents

- evals.json
- Assertions that can be checked
- Paired evaluation protocol
- Failure classification
- Content sufficiency test

## evals.json

**Definition.** `evals/evals.json`: realistic task prompts with the
expected outcome and objective assertions, in the shape Anthropic's
skill-creator tooling uses
([skill-creator][skill-creator], [evaluating skills][evaluating]):

```json
{
  "skill_name": "write-justfiles",
  "evals": [
    {
      "id": 1,
      "prompt": "Add a `test` recipe that forwards extra args to pytest",
      "expected_output": "A recipe using a variadic parameter...",
      "assertions": ["Uses `*args` or `+args`", "Quotes args"]
    }
  ]
}
```

**Use when.** Every skill. Write the evals before most of the content;
Anthropic recommends building evaluations first, with at least three
scenarios ([best practices][anthropic-bp]).

**Do not use when.** Never present eval files as results; they are
inputs.

**Example.** At least five cases: typical requests with concrete inputs
(file snippets, symptoms, commands), a stress case that tempts a known
wrong fix, and one near-miss that must not trigger the skill.

**Cost removed.** Skills tuned to imagined problems.

**Verify.**

1. `python3 -c "import json,sys; json.load(open(sys.argv[1]))"
   evals/evals.json` parses.
1. Each eval maps to at least one card in the routing table.

## Assertions that can be checked

**Definition.** Each assertion names an observable fact about the
transcript or produced files: a construct used, a command run, a file
changed or unchanged, a failure avoided.

**Use when.** Writing any assertion.

**Do not use when.** The assertion is "the response is helpful",
"follows best practices", or the skill's own wording; graders cannot
check those consistently.

**Example.**

```json
"assertions": [
  "Runs allocation assertions with DOTNET_TieredCompilation=0 or after warmup.",
  "Does not change the target framework or LangVersion.",
  "Reports bytes allocated before and after."
]
```

**Cost removed.** Evaluations that pass any answer.

**Verify.**

1. Two reviewers grading the same transcript reach the same verdict on
   each assertion.

## Paired evaluation protocol

**Definition.** Run the same prompts, fixtures, and environment with the
skill, with the previous version, and with no skill, and compare
observable outcomes per case.

**Use when.** Deciding whether a revision improves behavior.

**Do not use when.** Never substitute self-review or script tests for
agent runs. If trials are impossible, document the protocol and mark
the trials unexecuted.

**Example.** The protocol:

1. Freeze both package trees, catalog descriptions, fixtures, prompts,
   and graders, with identical repository instructions across
   conditions. Include direct requests, paraphrases, near-misses,
   incomplete inputs, a tempting shortcut, and a no-skill control.
1. Record model identifier, host version, discovery configuration,
   installed skills, permissions, tools, network access, and budgets; keep
   them fixed within each pair.
1. Use fresh state per trial, predeclare trial counts and retries,
   alternate condition order, and keep failures and timeouts.
1. Test selection (from metadata) separately from execution (skill
   loaded explicitly), so discovery errors do not pass as instruction
   errors.
1. Grade artifacts and forbidden effects first, then traces (skipped
   steps, redundant reads, unsupported completion claims). Grade blind to
   the condition when practical.
1. Report paired outcomes per case with the repetition count. Tokens
   and latency are secondary to correctness.

**Cost removed.** Revisions that read better but behave the same or
worse.

**Verify.**

1. The report lists, per case, both conditions' outcomes and the recorded
   environment.

## Failure classification

**Definition.** Classify each failed trial by the first stage that went
wrong, as far as the trace supports:

- **Selection**: the wrong skill loaded or the right one did not.
- **Loading**: selected, but the needed reference was never read.
- **Understanding**: read, but interpreted incorrectly.
- **Application**: understood, but the actions violated it.
- **Completion claim**: the report asserts an outcome the artifacts do not
  support.

**Use when.** Deciding what to change after a failed eval.

**Do not use when.** There is no trace; a final failure alone does not
identify its cause, so do not guess a stage.

**Example.** An agent claimed "zero allocations" but ran the assertion
at tier 0. Loading succeeded (it read the card); application failed (it
skipped `DOTNET_TieredCompilation=0`). Fix: move that step into the
SKILL.md workflow, not into another reference.

**Cost removed.** Fixing descriptions for application failures, or adding
checklists for selection failures.

**Verify.**

1. Each failure in the report has a stage and the trace line supporting
   it.

## Content sufficiency test

**Definition.** For every mode the skill advertises, a fresh agent
answers these from the skill and the target repository without
inventing facts:

1. What exact task and boundary am I handling?
1. Which version, source of truth, and configuration control it?
1. Which procedure and decision branch applies?
1. Which complete example, template, script, or official source do I use?
1. Which tempting wrong solutions must I reject, and why?
1. What evidence establishes each completion claim?
1. What remains unknown, unavailable, unauthorized, or unexecuted?

**Use when.** Auditing or finishing a skill.

**Do not use when.** Never answer a missing question with "follow best
practices"; add the domain material or narrow the skill's scope.

**Example.** For write-justfiles, question 4 fails if the skill
describes variadic parameters without a recipe that uses one and a
command that proves quoting; add the example and an argument probe that
prints each received argument. `just --dry-run` cannot prove quoting,
because nothing executes.

**Cost removed.** Gaps an agent fills by guessing.

**Verify.**

1. The seven answers exist for each advertised mode, each citing the
   card or file that answers it.

[skill-creator]: https://github.com/anthropics/skills/tree/main/skills/skill-creator
[evaluating]: https://agentskills.io/skill-creation/evaluating-skills
[anthropic-bp]: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
