---
name: define-requirements
description: >-
  Writes testable requirements: EARS statements, state and decision tables,
  measurable quality targets, and Given/When/Then acceptance criteria, checked
  by a bundled linter. Use when a change needs a spec or acceptance criteria.
  Not for architecture choices.
---

# Define Requirements

Turn a request into requirements that a reviewer can check and a test can
decide: each requirement has an ID, a source, one EARS statement with one
response, and at least one acceptance criterion that becomes a test.

## Workflow

1. Collect the controlling statements: the user's request and
   corrections, linked issues, existing public contracts. Current
   behavior is evidence of constraints, not of intent.
1. Build the glossary (identity and lifetime of each noun) and fix units
   and domains ([behavior models](references/behavior-models.md)).
1. Model behavior: a state transition table for anything with a
   lifecycle, a decision table for rules with three or more conditions,
   the linearization point for races, retry semantics, abuse cases at
   trust boundaries.
1. Write one requirement per response in the EARS form that matches its
   trigger ([requirement forms](references/requirement-forms.md)), with an
   ID and `[source: ...]`.
1. Write acceptance criteria as Given/When/Then observations at the
   contract boundary, including boundaries, failures, and races
   ([acceptance](references/acceptance.md)).
1. Record open decisions (`DEC-...`) with options and consequences for
   everything the sources do not settle.
1. Run `python3 scripts/check_requirements.py SPEC.md` until it reports
   `defects=0`, then deliver in the repository's issue or spec format.
1. If code exists or is being written, map each criterion to a test and
   run a discrimination check (break the behavior, see the test fail).

## Route the situation to a card

| Situation | Card |
| --- | --- |
| Requirement has no trigger | [Ubiquitous](references/requirement-forms.md#ears-ubiquitous) |
| Behavior responds to an event | [Event-driven](references/requirement-forms.md#ears-event-driven) |
| Behavior depends on a mode or state | [State-driven](references/requirement-forms.md#ears-state-driven) |
| Errors, failures, misuse | [Unwanted behavior](references/requirement-forms.md#ears-unwanted-behavior), [abuse cases](references/behavior-models.md#abuse-cases) |
| Behavior only in some configurations | [Optional feature](references/requirement-forms.md#ears-optional-feature) |
| State and event together | [Complex](references/requirement-forms.md#ears-complex) |
| Requirement bundles several responses | [One response](references/requirement-forms.md#one-response-per-requirement) |
| Spec uses MUST/SHOULD | [Normative keywords](references/requirement-forms.md#normative-keywords) |
| "Fast", "scalable", "reliable" | [Measurable quality](references/requirement-forms.md#measurable-quality-requirements), [vague terms](references/requirement-forms.md#vague-terms) |
| Where did this requirement come from? | [Sources](references/requirement-forms.md#sources-and-traceability) |
| Unknown policy, limit, or durability | [Open decisions](references/requirement-forms.md#open-decisions-and-out-of-scope-items) |
| Nouns with several meanings | [Glossary](references/behavior-models.md#glossary-with-identity-and-lifetime), [units](references/behavior-models.md#units-and-domains) |
| Entity with a lifecycle | [State table](references/behavior-models.md#state-transition-table) |
| Many interacting conditions | [Decision table](references/behavior-models.md#decision-table) |
| Concurrent operations | [Linearization point](references/behavior-models.md#linearization-point-for-races), [interleavings](references/acceptance.md#controlled-interleavings) |
| Retries, duplicate requests | [Retry semantics](references/behavior-models.md#retry-and-idempotency-semantics) |
| Writing acceptance criteria | [Given/When/Then](references/acceptance.md#givenwhenthen-criterion), [boundaries](references/acceptance.md#boundary-values), [observations](references/acceptance.md#observations-not-implementation-details) |
| Turning criteria into tests | [Mapping](references/acceptance.md#criterion-to-test-mapping), [discrimination](references/acceptance.md#discrimination-check) |

## Rules

- One `shall`, one response, one ID, one source per requirement.
- No invented numbers, limits, or policies; unknowns go to `DEC-` items.
- No implementation in requirements (classes, tables, libraries) unless
  the request constrains it.
- Every requirement has at least one acceptance criterion; every
  criterion references existing requirements and is observable at the
  contract boundary.
- Specify races by their linearization point and test them with a
  barrier; sleeps make the test flaky.
- Say whether each statement describes desired or current behavior.

## Bundled tools

- `scripts/check_requirements.py SPEC.md [--json]`: counts requirements,
  EARS patterns, and defects (missing source, non-EARS, several `shall`,
  vague terms, TBD, unverified requirements, bad criteria); exit 0 clean,
  1 defects, 2 unreadable.
- `assets/examples/`: the worked export-cancellation spec (0 defects), its
  vague first draft, a reference implementation, one acceptance test per
  criterion, and `verify.sh`, which also breaks the implementation to
  prove the tests discriminate.

## References

- [Requirement forms](references/requirement-forms.md): line format, the
  six EARS patterns, one response, normative keywords, measurable quality,
  vague terms, sources, open decisions.
- [Behavior models](references/behavior-models.md): glossary, units, state
  and decision tables, linearization points, retries, abuse cases.
- [Acceptance criteria](references/acceptance.md): Given/When/Then,
  test mapping, interleavings, boundaries, observations, discrimination.

## Completion evidence

The deliverable contains the glossary, models used, requirements,
acceptance criteria, and open decisions; the checker output with
`defects=0`; and, when code exists, the test run showing each criterion's
test and the discrimination check result.
