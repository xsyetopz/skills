# Revise accepted software requirements or design

A software phase baseline is a recorded requirements, design, or implementation
version. A change request records why that version needs revision, who may
authorize a scope change, and which later checks become invalid. It is not
automatically a GitHub pull request or permission to rewrite Git history.

Sequential software phase-completion checks establish fixed versions of
requirements, design, or implementation; they do not make baselines infallible.
Use controlled reopening instead of silent downstream redesign.

## Trigger

Open a change request when downstream evidence shows any of these:

- requirement is missing, contradictory, or untestable;
- design cannot satisfy a requirement;
- interface/dependency/lifetime model is infeasible;
- required external behavior differs from the baseline;
- security/performance/platform constraint invalidates the design;
- accepted scope must change.

Implementation defects that conform to a valid design do not require upstream
change control; fix them within the current phase.

## Impact analysis

A change request identifies:

1. originating evidence;
1. affected requirement/design IDs;
1. root cause;
1. proposed baseline change;
1. downstream artifacts invalidated;
1. tests/evidence that must be rerun;
1. schedule/resource impact if relevant;
1. authority needed to accept scope/requirement changes.

## Reopening rule

Reopen the earliest affected phase, revise and re-review its baseline, then
replay every downstream phase completion check whose assumptions changed. Do not
patch the latest phase and leave contradictory frozen documents behind.

Use `assets/software-baseline-change-request.template.md`.
