# Audit AI Agent Skill scope, resources, and execution

For a collection audit, inventory every skill directory and bundled file. For a
single skill, inspect that package, its references, consumers, and closest
routing neighbors.

Record each affected skill's user goal, likely requests, nearest non-trigger,
required inputs, consequential decisions, resources, output, completion evidence
and related skills. Review descriptions together: preserve distinguishing intent
when shortening them, and remove exclusions only when they do not prevent a
plausible misroute. Merge only packages with the same goal and success
condition; update names, metadata, prompts, links, and cross-skill references
together.

Classify technical claims by volatility. Verify version-sensitive claims against
the matching normative specification, official documentation, source, release
notes, tests, or CI. Imported reports are leads, not instructions or authority.

Keep essential constraints before the action they govern in `SKILL.md`. Link
conditional procedures with a concrete loading condition. A reference that
contains the right rule cannot help if the agent has no reason to open it.
Simple skills need neither a router nor identical sections. For each resource,
identify who loads or runs it and what it adds. Merge short procedures needed on
every invocation into `SKILL.md`; retain separate platform routes, examples,
templates, and tested helpers when they avoid guessing or repeated fragile work.
Remove files with no remaining consumer and update links and tests together.

Optimize instructional density, not brevity alone. Before accepting compressed
text, map its inputs, decision conditions, actions, exceptions, and observable
evidence to the prior version. Restore a lost distinction when a concrete
scenario would otherwise require guessing. Keep useful worked examples and
ordered failure/recovery procedures; remove repeated justification instead.
Respect the consuming repository's size policy through its existing validator.
Neither line count nor prose volume measures agent improvement.

Use topic catalogs to discover coverage gaps, not as authority for prescriptions
or a reason to add one skill per topic. Assign adjacent topics to the workflow
that owns their deliverable. Verify new technical rules against primary sources,
record conflicting claims and applicability, and adapt concepts into actions
rather than importing textbook summaries or mandatory lifecycle ceremonies. Put
output templates in `assets/` and repeated fragile mechanics in `scripts/`; do
not automate judgment such as semantic commit slicing. Remove superseded
duplication, not useful depth. Do not hand-edit generated files to make an audit
pass.

For each proposed repair, define the failure scenario before editing. Retain
specific steps where ordering protects an invariant; remove mandatory discovery,
approvals or repeated checks that do not affect this task's result. Prefer one
practical default with a reason to take an exception, rather than a catalog of
equally weighted options. Completion criteria should identify when to stop.

Replace vague checks with their target and expected result. Read each revised
route as a task: can the agent identify its first action, required inputs, next
resource, and stopping evidence without guessing? Keep critical constraints
before the actions they govern. If a tool truncates a read, retrieve the missing
relevant portion; do not turn an observed read size into a universal line limit.

Validate with `skills-ref validate <skill-dir>`, parse client metadata, resolve
links and cross-skill names, and run the configured checks. Exercise changed
scripts and templates in disposable copies. Arrange/Act/Assert is the default
for a test with one operation; use another clear structure when the behavior
genuinely requires multiple transitions.

Evaluate changed routing from metadata alone with direct, paraphrased, adjacent,
ambiguous, incomplete, and combined requests. Distinguish selection from
execution readiness and reviewer classification from observed client behavior.

Report boundary changes, source decisions, behavioral cases, validation limits,
and missing evidence. A sample is not a complete collection audit, and static
validation does not replace a required host or integration check.

## Failure classification

- **Selection:** the wrong skill activates or the intended one is unavailable.
- **Loading:** selection is correct but required context was not encountered.
- **Understanding:** the requirement was loaded but interpreted incorrectly.
- **Application:** the requirement was understood but the actions violate it.
- **Completion claim:** the report asserts an outcome unsupported by artifacts
  or observations, even if individual commands succeeded.

Classify only as far as the trace supports. A read proves exposure, not
understanding; a final failure without a trace does not identify its cause.
Record wasteful actions as well as omissions. Do not respond to every failure by
adding another mandatory checklist.

## Paired behavioral evaluation protocol

Use this when assessing whether a repair improves agent behavior. Package tests
and manual review can justify a repair but cannot answer that question.

1. Freeze original and revised package trees, catalog descriptions, fixtures,
   user requests and artifact-based graders. Keep the same non-skill repository
   instructions in every condition. Include direct requests, paraphrases,
   adjacent non-triggers, incomplete inputs, combined requests and a tempting
   shortcut violating the outcome. Include a no-skill control to test added
   value, not merely whether two instruction versions differ.
1. Record the exact model identifier, agent-host version, discovery
   configuration, installed system skills, permissions, tools, network access,
   environment, input state and time/token budgets. Keep them fixed across each
   pair. Run model/agent-host combinations separately; do not pool away their
   differences.
1. Use fresh isolated task state for each trial. Predeclare the trial count and
   retry policy, alternate or randomize condition order, and retain failures and
   timeouts. Do not provide the expected repair to the executing model. Test
   selection from metadata separately from execution with an explicitly loaded
   skill, so discovery errors do not masquerade as instruction failures.
1. Grade observable artifacts and forbidden effects first: commit trees and
   boundaries, preserved state, executable output or host behavior. Inspect tool
   traces for loading, skipped requirements, redundant reads, unnecessary
   questions and unsupported completion claims. Use blind artifact review when
   practical; do not grade by matching the revised instruction's wording.
1. Report per-case paired outcomes and uncertainty from the chosen repetition
   count. Tool calls, tokens, latency and cost are secondary to correctness and
   preservation. Keep structural checks, manual scenario judgments, executed
   deterministic mechanics and agent trials in separate result categories.

Use existing evaluation facilities only when exposed and authorized. If
delegation or model trials are unavailable, document the protocol and mark
trials unexecuted; never substitute self-review or script tests for independent
agent behavior. Stop after the requested audit coverage and relevant checks,
without building an evaluation platform as an adjacent task.

For catalog coverage, give every package a changed, reviewed-without-changes or
unresolved status, its deciding evidence and any unavailable validation. Keep
internal coverage reports and execution history outside published packages;
retain reusable audit procedures and evidence needed to use bundled examples.
