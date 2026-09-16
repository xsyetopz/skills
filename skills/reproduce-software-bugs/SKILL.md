---
name: reproduce-software-bugs
description: >-
  Use when constructing or reducing an independently runnable reproduction of
  a specific software defect. Preserve the same failure while minimizing
  necessary source, input, dependencies, and execution steps. Not for a
  tutorial example or replacing production tests.
---


# Reproduce Software Bugs

Create an isolated, independently runnable artifact that demonstrates the same
defect and distinguishes it from setup failures. Reduce only while the failure
signature and relevant boundary remain intact.

## Operating contract

- Define the exact failure signature before removing anything. A generic
  exception, crash, or nonzero exit is not automatically the same bug.
- Start from a confirmed failing case and preserve immutable inputs, versions,
  configuration, platform constraints, and timing/concurrency conditions that
  matter.
- Remove one dependency or dimension at a time and rerun both failure and
  environment sanity checks.
- Do not mock away the failing integration, replace real behavior with an
  explanation, or hard-code a failure unrelated to the product defect.
- Keep credentials, customer data, proprietary code, and large artifacts out of
  the reproducer; synthesize or sanitize without changing the failure.

## Workflow

```mermaid
flowchart TD
    F[Confirmed original failure] --> S[Define signature and sanity checks]
    S --> I[Isolate copy and pin environment]
    I --> R[Remove one input, dependency, or layer]
    R --> T{Same failure signature?}
    T -->|Yes| K[Keep reduction]
    T -->|No| U[Restore removed element]
    K --> R
    U --> R
    K --> P[Package commands, expected/actual, and limits]
```

## Procedure

1. Record the original command, environment, revision, versions, input identity,
   expected behavior, actual failure, and distinguishing signature. Confirm it
   more than once when nondeterministic.
1. Create an isolated copy or minimal project using the same failing boundary.
   Pin required dependencies/toolchain and add a sanity check that distinguishes
   setup failure.
1. Reduce systematically: files/modules, dependencies, input fields/bytes,
   configuration, data volume, timing, platform layers, and steps. Change one
   dimension when possible; after each reduction rerun the failure signature and
   sanity check.
1. Preserve a control or known-good variant when useful. For races, retain a
   controlled schedule/barrier or repeat rule; do not turn timing into a
   sleep-only coincidence.
1. Replace confidential/proprietary data with generated data only after proving
   the same internal condition and signature. Remove credentials and unrelated
   network dependencies.
1. Package the smallest practical complete project under normal native structure
   with exact setup/run/cleanup commands, expected versus actual result,
   versions, and limits. Verify from a fresh directory or environment.
1. Link the reproducer back to the production boundary and state what it does
   not model. Do not replace the repository’s regression test; use the
   reproducer to diagnose and derive the proper test.

## Read only the material needed

| Situation | Read or use |
| --- | --- |
| Reducing inputs/dependencies and packaging a complete reproducer | [Reduction and packaging](references/reduction-and-packaging.md) |
| Choosing reduction dimensions and failure signatures | [Decision guide](references/decision-guide.md) |
| Using complete deterministic, race, build, and integration examples | [Worked examples](references/worked-examples.md) |
| Verifying same defect and fresh-environment execution | [Verification and evidence](references/verification-and-evidence.md) |
| Avoiding generic errors, mocks, and setup failures | [Failure modes](references/failure-modes.md) |
| Applying enterprise data and disclosure controls | [Enterprise operation](references/enterprise-operation.md) |
| Checking source guidance | [Source index](references/source-index.md) |

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

- No output template is mandatory. Preserve the repository’s established format.

Copy or adapt assets into the target workspace. Do not edit the installed skill
as a substitute for changing the requested repository.

## Completion evidence

- Original and reduced commands, versions, inputs, and failure signature.
- Complete isolated project/files needed to run.
- Sanity check that distinguishes setup from target defect.
- Reduction log or rationale for remaining elements.
- Fresh-environment result and nondeterminism rule where applicable.
- Security/privacy sanitization and known differences from production.

## Stop or escalate

- The original defect cannot be confirmed or distinguished from setup failure.
- Reduction would require disclosing sensitive/proprietary data without an
  approved sanitization path.
- The failing boundary is unavailable and a mock would remove the defect.
- The remaining nondeterminism has no reproducible classification rule.

Do not claim completion while a required check is failed, unattempted, or
unavailable. State the exact evidence and the remaining boundary instead of
promoting a narrower result into a broader claim.
