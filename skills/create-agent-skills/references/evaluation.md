# Evaluation

Static checks show a package is well formed. Only runs on the target host
show that it changes what an agent does.

## Contents

- [Output evals](#output-evals)
- [Paired runs](#paired-runs)
- [Classifying a failure](#classifying-a-failure)
- [Auditing an existing skill](#auditing-an-existing-skill)

## Output evals

`evals/evals.json`, in the shape Anthropic's skill-creator uses
([evaluating skills][evaluating]):

```json
{
  "skill_name": "write-justfiles",
  "evals": [
    {
      "id": 1,
      "prompt": "Add a test recipe that forwards extra args to pytest",
      "expected_output": "A recipe with a variadic parameter, quoted.",
      "files": ["evals/files/basic/justfile"],
      "assertions": [
        "Uses a *args or +args parameter.",
        {"text": "just --dry-run test -k x succeeds",
         "check": "just --dry-run test -k x"}
      ]
    }
  ]
}
```

- Write three to five cases aimed at the mistakes the skill exists to
  prevent. A case that any capable model passes without the skill
  measures nothing.
- Include one case that tempts a known wrong fix.
- Each assertion names an observable fact: a command run, a file changed
  or unchanged, a construct used. "Is helpful" or "follows best
  practices" cannot be graded consistently.
- Prefer a `check` command where the fact is mechanical. Leave judgment
  to the grader only where it needs meaning.
- Keep fixtures to the few files the prompt needs.

## Paired runs

Run the same prompts with the skill and without it, or against the
previous version, with everything else fixed: model, host version,
installed catalog, permissions, and fixtures.

- Use fresh state per trial and keep failures and timeouts in the count.
- Test selection separately from execution. Load the skill explicitly
  for output evals, so a trigger miss does not look like a bad
  instruction.
- Report paired outcomes per case with the number of runs. Tokens and
  time come second to correctness.
- A revision that does not beat the no-skill baseline is not an
  improvement, however much better it reads.

## Classifying a failure

Find the first stage that went wrong in the trace, then fix that stage.

- Selection: the skill did not load or the wrong one did. Fix the
  description.
- Loading: the needed reference was never read. Move the rule into the
  body or give the reference a sharper load condition.
- Application: the rule was read and not followed. Make it a specific
  check near the top, give its reason, or move the step into a script.
- Completion claim: the report says something the artifacts do not
  support. Add a check the agent must run and quote.

Adding checklists does not fix a selection failure, and rewording the
description does not fix an application failure.

## Auditing an existing skill

Cut before adding.

1. For each line, ask whether a capable model would do this anyway.
   Delete the line if so. Textbook explanations, definitions of common
   terms, and generic process advice go first.
1. Delete routing tables that repeat headings, "when to use" sections,
   completion-report templates, and scope paragraphs that repeat the
   description.
1. Delete demo projects and verifier scripts that prove the skill's
   examples rather than the user's code.
1. Find skills with overlapping triggers and merge them, keeping one
   reference per variant.
1. Move surviving gotchas to the top of the body, each as mistake, fix,
   and reason.
1. Rewrite the description, then run trigger and output evals with and
   without the skill.

Before deleting, keep any verified fact that the model gets wrong, with
its source, in the body or the matching reference.

[evaluating]: https://agentskills.io/skill-creation/evaluating-skills
