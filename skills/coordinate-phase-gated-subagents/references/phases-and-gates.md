# Phases and gates

The five sequential phases of the Waterfall model and the gate that
closes each one. Parallel work happens only inside a phase.
`scripts/check_gate.py` checks gate records; the templates are in
`assets/`.

## Contents

- Phase 1: requirements baseline
- Phase 2: design baseline with ownership
- Phase 3: implementation by work item
- Phase 4: integration and verification
- Phase 5: release preparation
- Gate decision from evidence
- Baseline change request

## Phase 1: requirements baseline

**Definition.** Each requirement record has:

- a stable ID;
- one observable obligation;
- its source;
- an acceptance condition;
- a verification method: test, analysis, inspection, or measurement.

The accepted set is frozen as the requirements baseline.

**Use when.** The user asked for phase-gated multi-agent delivery and the
requirements are not yet written down.

**Do not use when.** An accepted requirements document exists. Reference
it instead of rewriting it; to write requirements, see
`$define-requirements`.

**Example.** Parallel analysts each cover one area: API behavior,
compatibility, security, performance, or environment. The orchestrator
merges their findings into
[`software-requirements-baseline.template.md`][req-template]:

```text
REQ-003  wordcount --top N prints the N most frequent words.
Source: issue #41. Acceptance: `--top 2` on sample.txt prints
"3 the\n2 dog". Verification: test (tests/test_cli.py::test_top).
```

**Cost removed.** Implementers guessing at behavior. The change requests
opened after phase 1 measure the late rework that remains.

**Verify.**

1. Every requirement has an acceptance condition and a verification
   method.
1. The gate record lists the review of the baseline as passed.

## Phase 2: design baseline with ownership

**Definition.** The design fixes the pieces that parallel work depends
on:

- interfaces;
- data invariants;
- errors and concurrency;
- the dependency direction;
- the work breakdown, with the paths each item owns;
- the integration order.

Risky assumptions get a small feasibility probe before the design is
accepted.

**Use when.** Parallel implementation is about to start.

**Do not use when.** The work is one item; skip this skill entirely.

**Example.** The work breakdown goes in a plan file that
`check_work_items.py` accepts. From `assets/examples/work-items.json`:

```text
wave 1: parser, store
wave 2: cli
0 error(s)
```

**Cost removed.** Workers building incompatible interfaces. The checker
catches overlapping ownership before work starts: it rejects the conflict
plan for a shared `src/common.py`.

**Verify.**

1. `check_work_items.py PLAN.json` exits 0.
1. Each interface named in the plan has a definition in the design
   baseline.

## Phase 3: implementation by work item

**Definition.** Each worker gets one work item containing:

- the requirement IDs;
- the design baseline version;
- the base revision;
- the paths it owns;
- its dependencies;
- a local check command.

The worker changes only what it owns and returns the worker result (see
[subagents][result]). TDD and refactoring happen inside the item.

**Use when.** The design gate has closed.

**Do not use when.** An item needs to change an interface. That is a
[baseline change](#baseline-change-request), not a local edit.

**Example.** `assets/subagent-software-work-item.template.md` holds the
brief. The waves from the plan decide which items start together.

**Cost removed.** Scope creep and silent interface changes, visible as
edits outside `owns` in the item's diff.

**Verify.**

1. `git diff --name-only BASE..ITEM` lists only paths inside the item's
   `owns`.
1. The item's local check ran, and the command and output are in its
   result.

## Phase 4: integration and verification

**Definition.** Merge the items in the planned order. Group failures by
root cause into queues and give each queue one owner. Fill in the
verification matrix: requirement, command, environment, and result.

**Use when.** All implementation items are done or explicitly deferred.

**Do not use when.** You would hand one worker the whole unpartitioned
failure log. Capture it once and split it by ownership.

**Example.** `assets/examples/gate-verification.json` has one passed,
one unavailable (staging credentials), and one not-run condition:

```text
gate integration-verification: OPEN
  C2: unavailable
  C3: not_run
  R3: no passed verification
```

**Cost removed.** "Verified" claims resting on checks that never ran.

**Verify.**

1. `check_gate.py` exits 0 on the verification record, or the report
   states each open reason.

## Phase 5: release preparation

**Definition.** Build the release artifacts, notes, and version bump from
the verified revision. Publishing is a separate action the user must
approve.

**Use when.** The verification gate has closed.

**Do not use when.** You would publish, tag on a remote, or deploy without
explicit approval. Those actions are outward-facing
(`$manage-git-hosting`).

**Example.** Write changelog entries with `$update-changelogs`. The
release gate requires the artifact digest to equal the one verified in
phase 4.

**Cost removed.** Releasing a build other than the one verified.

**Verify.**

1. The release record names the verified revision and the artifact
   digest.

## Gate decision from evidence

**Definition.** A gate closes only when every required condition has
`passed` evidence with a recorded command, and every requirement is
traced to a passed condition. Keep the other statuses distinct; each
needs a different next step:

- `failed`: fix the cause;
- `unavailable`: get access, or ask;
- `not_run`: run the check.

**Use when.** At the end of each phase.

**Do not use when.** You would close a gate because "it probably works".
An unavailable check is not a pass.

**Example.** `test_each_non_pass_status_keeps_gate_open` shows each of
the three statuses keeping the gate open; `gate-implementation.json`
closes.

**Cost removed.** Phases that advance on assumed evidence.

**Verify.**

1. Keep the gate record in the phase-completion template, and run
   `check_gate.py` on it.

## Baseline change request

**Definition.** A request to change the frozen requirements or design.
It records:

- the triggering evidence;
- the affected IDs;
- the root cause;
- the change proposed;
- the artifacts it invalidates;
- the checks to rerun;
- who can approve it.

Approval reopens every gate downstream of the change.

**Use when.** A requirement is contradictory or untestable, or the
design cannot meet it.

**Do not use when.** You would adjust a test to match the code. That
weakens a check; it does not change the baseline.

**Example.** Template: `assets/software-baseline-change-request.template.md`.
A change to the `store` interface lists `cli` as invalidated, so `cli`
returns to wave 2.

**Cost removed.** Silent contract drift across workers.

**Verify.**

1. Every reopened work item has a new result against the new baseline
   version.

[req-template]: ../assets/software-requirements-baseline.template.md
[result]: subagents.md#worker-result-contract
