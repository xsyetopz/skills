# Decide whether a development phase may advance

A phase gate is the required completion checks for the current development
phase. Use the existing project or host status format; the words below explain
conditions, not a new state schema.

## Separate completion from evidence availability

- Complete: each required criterion has evidence appropriate to that property
  and no unresolved contradiction prevents advancement.
- Failed: a required check contradicts the criterion. Diagnose the failure; do
  not weaken the criterion to match current implementation.
- Not run or unavailable: required evidence has not been obtained. State which
  condition prevents execution; neither state counts as passing.
- Reopened: a changed requirement, design decision, or input version invalidates
  prior evidence. Repeat the affected checks before advancing again.

A skipped check needs its actual reason. A timeout, cancelled worker, missing
tool, unattempted test, and reproducible defect are different outcomes.
Percentages or a passing subset cannot substitute for mandatory criteria.

## Match evidence to the criterion

Use runtime observations for behavior, compiler/static checks for the properties
they establish, artifact inspection for packaging, and source/contract analysis
for design obligations. No universal evidence ranking makes unit tests prove
migration recovery, hardware execution, or deployment. An agent assertion,
preferred architecture, comment, or test count does not establish those claims.

## Keep the smallest useful completion record

Identify the input and candidate versions, required conditions, exact checks,
observed results and evidence locations, unresolved findings, and any actual
project decision authority. Use the existing format or the supplied [completion
template](../assets/software-phase-completion.template.md). Do not invent
stakeholder approval, waive a requirement implicitly, or turn unavailable
evidence into success. A passing gate grants no extra write, commit,
publication, or deployment authority.

Plan verification methods during requirements and concrete environments during
design. The implementation phase includes local TDD and refactoring; integration
verification checks the combined candidate rather than postponing all testing.

Sources: [NASA
lifecycle](https://www.nasa.gov/reference/3-0-nasa-program-project-life-cycle/)
and [systems engineering][systems-engineering].

[systems-engineering]:
https://www.nasa.gov/reference/2-0-fundamentals-of-systems-engineering/
