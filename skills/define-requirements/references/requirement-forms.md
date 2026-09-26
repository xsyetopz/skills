# Requirement forms

Writing each requirement so it is atomic, testable, and traceable.
`scripts/check_requirements.py` checks the forms below. The worked example
is [`export-cancellation-spec.md`][spec] (0 defects);
[`vague-spec.md`][vague] shows what the checker rejects (16 defects).

## Contents

- Requirement line format
- EARS ubiquitous
- EARS event-driven
- EARS state-driven
- EARS unwanted behavior
- EARS optional feature
- EARS complex
- One response per requirement
- Normative keywords
- Measurable quality requirements
- Vague terms
- Sources and traceability
- Open decisions and out-of-scope items

## Requirement line format

**Definition.** Each requirement is one list item:
`REQ-<ID> [source: <where it came from>] <EARS statement>`. IDs are
unique and stable; indent wrapped continuation lines.

**Use when.** Writing requirements that the checker and reviewers can
reference, unless the repository has its own issue or spec format.

**Do not use when.** The project prescribes another template. Follow it
and keep the same rules: ID, source, one response, acceptance link.

**Example.**

```text
- REQ-EXP-002 [source: issue 42] When a job is cancelled, the export
  service shall leave the destination's previous contents unchanged.
```

**Cost removed.** Requirements that cannot be referenced from tests,
reviews, or plans.

**Verify.**

1. `python3 scripts/check_requirements.py SPEC.md` reports no duplicate
   IDs and no missing sources.

## EARS ubiquitous

**Definition.** Always-active behavior: `The <system> shall <response>.`
(Easy Approach to Requirements Syntax, [Mavin et al., RE'09][ears-paper];
[EARS patterns][ears]).

**Use when.** The behavior has no trigger or state condition.

**Do not use when.** The behavior applies only after an event or in a
state; the ubiquitous form hides the condition.

**Example.** `The export service shall write exports in UTF-8.`

**Cost removed.** Conditions discovered during testing instead of during
specification.

**Verify.**

1. The checker counts it under `pattern ubiquitous`.

## EARS event-driven

**Definition.** `When <trigger>, the <system> shall <response>.` The
response is required when the trigger occurs.

**Use when.** The behavior responds to a request, message, timer, or
input.

**Do not use when.** The trigger is a persistent state (use `While`) or an
unwanted situation (use `If ... then`).

**Example.**

```text
When a cancel request arrives while a job is writing, the export service
shall change the job to cancelled and remove the job's temporary file.
```

**Cost removed.** Ambiguity about when the behavior applies.

**Verify.**

1. The checker counts it under `pattern event-driven`.

## EARS state-driven

**Definition.** `While <state>, the <system> shall <response>.` The
response is required for as long as the state holds.

**Use when.** The behavior depends on a mode or lifecycle state (offline,
cancelled, maintenance).

**Do not use when.** The state is instantaneous; use an event.

**Example.**

```text
While a job is cancelled or published, the export service shall treat a
repeated cancel request as a no-op that returns the current outcome.
```

**Cost removed.** Missing behavior for repeated or late events.

**Verify.**

1. The checker counts it under `pattern state-driven`.

## EARS unwanted behavior

**Definition.** `If <condition>, then the <system> shall <response>.`,
for errors, failures, and misuse.

**Use when.** Specifying behavior on invalid input, dependency failure,
timeouts, or attacks.

**Do not use when.** The condition is an expected, normal event; use
`When`.

**Example.**

```text
If validation of the export fails, then the export service shall remove
the job's temporary file and report the validation error without
publishing.
```

**Cost removed.** Error behavior left to the implementer's guess.

**Verify.**

1. The checker counts it under `pattern unwanted`; each such requirement
   has an acceptance criterion that injects the failure.

## EARS optional feature

**Definition.** `Where <feature is included>, the <system> shall
<response>.`, for behavior present only in some configurations or
products.

**Use when.** A feature flag, edition, or hardware option enables the
behavior.

**Do not use when.** The "feature" is a runtime state; use `While`.

**Example.** `Where audit logging is enabled, the export service shall
record the requesting user of each cancellation.`

**Cost removed.** Configuration-specific behavior asserted for all
configurations.

**Verify.**

1. The checker counts it under `pattern optional`; acceptance tests run
   with the feature on and off.

## EARS complex

**Definition.** A combination of keywords, most often `While <state>, when
<trigger>, the <system> shall <response>.`

**Use when.** A response needs both a state and a trigger.

**Do not use when.** It would nest more than two conditions. Split it into
several requirements or use a decision table (see
[behavior models](behavior-models.md#decision-table)).

**Example.** `While the service is in maintenance mode, when an export
request arrives, the export service shall reject it with a retry-after
time.`

**Cost removed.** Missing interactions between modes and events.

**Verify.**

1. The checker counts it under `pattern complex`.

## One response per requirement

**Definition.** Each requirement contains exactly one `shall` and one
observable response. The response may have parts that always happen
together.

**Use when.** Writing any requirement.

**Do not use when.** No exception. Never join independent responses with
"and shall": one can pass while the other fails, and tests cannot report
which.

**Example.** The checker rejected an earlier draft of REQ-EXP-003,
"...shall report that publication has started and shall not change the
job's outcome", until it became one response: "shall report that
publication has started and keep the job's outcome unchanged".

**Cost removed.** Requirements that are partly met.

**Verify.**

1. The checker reports `must contain exactly one 'shall'`.

## Normative keywords

**Definition.** MUST/SHALL (required), SHOULD (recommended, with valid
exceptions), and MAY (optional), as defined in [RFC 2119][rfc2119].
[RFC 8174][rfc8174] clarifies that they carry these meanings only in
capitals.

**Use when.** The document adopts BCP 14 keywords (APIs, protocols).

**Do not use when.** The requirements use EARS `shall` throughout. Mixing
the two vocabularies invites disputes about strength.

**Example.** `The client MUST send the Idempotency-Key header on POST
/exports.`

**Cost removed.** Arguments over whether "should" is mandatory.

**Verify.**

1. `rg -n '\b(must|should|may)\b' SPEC.md` finds no lowercase keywords
   used as requirements.

## Measurable quality requirements

**Definition.** Performance, availability, and capacity requirements
state the indicator, target, measurement window, and workload, like
service level objectives
([Google SRE: SLOs][sre-slo]).

**Use when.** The request includes expectations about speed, scale,
availability, or cost.

**Do not use when.** No stakeholder gave a number. Record an open decision
instead of inventing one.

**Example.**

```text
- REQ-EXP-010 [source: SLO doc 2026-Q3] The export service shall return
  a cancel response within 200 ms for 99% of requests over a 28-day
  window at up to 50 requests per second.
```

**Cost removed.** "Fast" as an untestable goal.

**Verify.**

1. The requirement names the indicator, threshold, percentile or ratio,
   window, and load; its acceptance criterion names the measuring tool.

## Vague terms

**Definition.** Words with no test: fast, efficient, user-friendly,
robust, appropriate, as needed, etc., and/or.

**Use when.** Reviewing any requirement.

**Do not use when.** The word is part of a quoted external name.

**Example.** "Users can cancel exports quickly" becomes REQ-EXP-001 plus
the measurable REQ-EXP-010, or an open decision if nobody gave a number.

**Cost removed.** Disputes at acceptance time.

**Verify.**

1. The checker lists `uses vague term` defects: none in the worked spec,
   four in the vague draft.

## Sources and traceability

**Definition.** Each requirement names its origin: a user statement, an
issue, an existing public contract, a regulation, or a recorded
decision.

**Use when.** Writing any requirement. An untraceable requirement is
often the author's preferred implementation.

**Do not use when.** No exception, and "best practice" is never a source.

**Example.** `[source: issue 42]`, `[source: design review 2026-09-01]`,
`[source: RFC 9110 section 9.3.5]`.

**Cost removed.** Scope creep disguised as requirements.

**Verify.**

1. The checker reports `has no [source: ...]`.

## Open decisions and out-of-scope items

**Definition.** List choices the evidence does not settle as `DEC-<ID>`
items with the options and their consequences. State excluded behavior
explicitly.

**Use when.** No source decides overwrite policy, durability, ordering,
compatibility, retention, limits, or authorization.

**Do not use when.** You would fill the gap with a guess. `TBD` inside a
requirement is a defect; a `DEC` entry is not.

**Example.**

```text
- DEC-EXP-001: Crash recovery of in-flight jobs is not specified; an
  atomic rename alone does not make publication durable across power
  loss.
```

**Cost removed.** Silent assumptions that become bugs.

**Verify.**

1. The checker reports `open TBD marker` for TBDs inside requirement
   text; each decision appears under an "Open decisions" heading.

[ears]: https://alistairmavin.com/ears/
[ears-paper]: https://doi.org/10.1109/RE.2009.9
[rfc2119]: https://www.rfc-editor.org/rfc/rfc2119
[rfc8174]: https://www.rfc-editor.org/rfc/rfc8174
[sre-slo]: https://sre.google/sre-book/service-level-objectives/
[spec]: ../assets/examples/export-cancellation-spec.md
[vague]: ../assets/examples/vague-spec.md
