# Delivery process

We deliver larger features in phases (requirements, design,
implementation, integration and verification, release). A phase starts
only after the previous phase's gate closes on recorded evidence.

## Work plan

The implementation phase is split into work items, each done by one
worker in its own worktree. The plan is `plan/work-items.json`:

```json
{
  "phase": "implementation",
  "items": [
    {"id": "a", "phase": "implementation", "owns": ["src/a/"],
     "depends_on": []}
  ]
}
```

`owns` lists the paths an item may write: a directory ends with `/`,
anything else is one file. Items without a dependency path between them
run in the same wave, so they must not own overlapping paths.

## Gate records

Each gate is recorded in `gates/<phase>.json`:

```json
{
  "phase": "integration-verification",
  "conditions": [
    {"id": "C1", "required": true,
     "evidence": {"status": "passed", "command": "...", "result": "..."}}
  ],
  "requirements": [{"id": "R1", "verified_by": ["C1"]}]
}
```

`status` is one of `passed`, `failed`, `unavailable`, `not_run`.

## Change requests

A change to a frozen baseline (requirements or design) is proposed as a
Markdown file in `change-requests/` that states the problem, the evidence,
the affected items, the work it invalidates, and the decision (pending
until the tech lead approves).
