---
name: {action-object, equal to the directory name}
description: >-
  {Third person. What it does with concrete verbs and objects, the trigger
  terms users type, and one "Not for ..." clause naming the nearest
  neighboring task. About 300 characters.}
---

# {Title}

{One paragraph: the outcome, the objects handled, and the rule that every
change is a construct card applied to observed evidence and verified.}

## Workflow

1. {Inspect: exact files and commands that establish the target's version
   and configuration.}
1. {Measure or reproduce: exact command and the metric or symptom.}
1. {Choose a card from the routing table below.}
1. {Pin behavior with a test or oracle before changing anything.}
1. {Apply one card; run its Verify steps.}
1. {Report with the evidence listed under Completion evidence.}

## Route evidence to a card

| Evidence | Card |
| --- | --- |
| {observable symptom} | [{card}](references/{file}.md#{anchor}) |

## Rules

- {Rule that prevents a known failure in this domain; add the reason only
  when it is not obvious.}

## Bundled tools

- `scripts/{name}.py ARGS`: {what it checks}; exit 0/1/2 meaning.
- `assets/examples/verify.sh {modes}`: {what each mode proves}.

## References

- [{Domain}](references/{file}.md): {which cards it holds}.

## Completion evidence

The report contains: {version and configuration}, {evidence of the
problem}, {cards applied}, {verification commands and results}, and
{anything not run, stated as not verified}.
