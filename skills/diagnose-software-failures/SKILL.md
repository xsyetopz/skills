---
name: diagnose-software-failures
description: >-
  Use when investigating software crashes, hangs, incorrect results,
  intermittent failures, or build failures whose cause is unknown. Reproduce
  the failure and distinguish competing causes. Not for a known mechanical
  fix, performance measurement alone, or Git bisect alone.
---


# Diagnose Software Failures

Establish the causal chain from an exact observed symptom to the first incorrect
state and owning subsystem. Use controlled observations to eliminate competing
explanations before changing production behavior.

## Operating contract

- Keep symptom, expected behavior, hypothesis, evidence, and established cause
  distinct. A user explanation is a hypothesis to test.
- Preserve the first useful error, stack, input, revision, environment, and
  state. Wrapper messages and downstream recovery may hide the initiating fault.
- Change one causal factor when possible. Do not accumulate speculative patches,
  retries, broad logging, dependency upgrades, or assertion changes.
- For intermittent failures, record attempts and conditions; one pass is not a
  fix.
- Diagnosis does not authorize mutation, production experiments, destructive
  cleanup, or disclosure of sensitive logs.

## Workflow

```mermaid
flowchart TD
    O[Exact observed failure] --> R[Reproduce same signature]
    R --> B[Locate first incorrect state]
    B --> H[Competing hypotheses]
    H --> X[Choose discriminating experiment]
    X --> E{Observation matches prediction?}
    E -->|No| H
    E -->|Yes| C[Establish causal chain]
    C --> F[Smallest authorized fix]
    F --> V[Regression + boundary verification]
    V --> D[Report evidence and remaining uncertainty]
```

## Procedure

1. Capture the exact operation, expected and actual result, error/stack, input
   identity, revision/build, configuration, environment, timing/concurrency
   conditions, and recent change context. Establish whether the failure exists
   in the baseline.
1. Reproduce with the narrowest command that preserves the same failure
   signature. Distinguish product failure from test setup, dependency,
   credential, infrastructure, or harness failure.
1. Trace backward from the symptom to the first incorrect state, ownership
   transfer, protocol mismatch, or violated invariant. Inspect source, call
   sites, generated/source relationships, and runtime state at that boundary.
1. Maintain a small hypothesis table. For each hypothesis, state a predicted
   observation that differs from alternatives. Select a debugger, trace,
   sanitizer, reduced input, controlled schedule, binary search, or targeted log
   that can observe it.
1. Run the experiment without changing expected behavior to fit the result.
   Update or discard hypotheses. When repeated actions produce no new
   information, improve the observation or change strategy rather than patching
   forward.
1. Once the cause is established, identify the owning layer and smallest correct
   repair. If implementation is authorized, add a regression check with an
   independent expected result, apply the fix, and run boundary-appropriate
   verification.
1. Report reproducer, first divergence, causal chain, source locations, fix,
   executed checks, and uncertainty. Keep infrastructure gaps and untested
   production conditions explicit.

## Read only the material needed

| Situation | Read or use |
| --- | --- |
| Designing discriminating experiments and stopping patch accumulation | [Causal investigation](references/causal-investigation.md) |
| Choosing debugger, trace, sanitizer, log, or reduction strategies | [Decision guide](references/decision-guide.md) |
| Using crash, deadlock, race, memory, build, and data-corruption examples | [Worked investigations](references/worked-examples.md) |
| Mapping diagnosis claims to evidence | [Verification and evidence](references/verification-and-evidence.md) |
| Avoiding retries, symptom patches, and harness conflation | [Failure modes](references/failure-modes.md) |
| Handling enterprise logs, incidents, and production boundaries | [Enterprise operation](references/enterprise-operation.md) |
| Reviewing a worked parser/default investigation | [Investigation example](assets/investigation-example.md) |
| Checking diagnostic tool sources | [Source index](references/source-index.md) |

## Additional specialized references

Read only the reference whose subject affects the current task.

| Reference | Use when |
| --- | --- |
| [Domain model and authority](references/domain-model.md) | Current implementation is evidence of state, not automatically the desired contract. |
| [Bundled resource catalog](references/resource-catalog.md) | Use this catalog to locate the exact skill-local files needed for the task. |

## Evaluation cases

Use [evaluation cases](references/evaluation-cases.md) for realistic activation,
near-miss, and instruction-conformance probes. These are maintained test inputs,
not claimed results.

## Bundled executable helpers

- No bundled script is mandatory. Use the target repository’s established tools.

Run a helper only for the contract it documents. Inspect arguments and output; a
zero exit status proves only the checks implemented by that helper.

## Bundled output material

- `assets/investigation-example.md`

Copy or adapt assets into the target workspace. Do not edit the installed skill
as a substitute for changing the requested repository.

## Completion evidence

- Exact reproducer and failure signature.
- Baseline comparison and first incorrect state.
- Hypotheses, discriminating experiments, and observed results.
- Causal chain and owning subsystem with source/runtime evidence.
- Authorized fix and regression verification, or diagnosis-only result.
- Uncertainty, unavailable checks, and production applicability limits.

## Stop or escalate

- The failure cannot be reproduced or observed enough to distinguish causes;
  report needed evidence rather than guessing.
- Production access, data, credentials, or experiments exceed authorization.
- A material expected-behavior decision is unresolved.
- The only remaining action is an unbounded retry/patch loop with no new
  evidence.

Do not claim completion while a required check is failed, unattempted, or
unavailable. State the exact evidence and the remaining boundary instead of
promoting a narrower result into a broader claim.
