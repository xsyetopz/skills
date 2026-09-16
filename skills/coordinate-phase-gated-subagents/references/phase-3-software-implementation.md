# Phase 3: implement the accepted software design

Goal: realize the frozen design without changing requirements or architecture by
stealth.

## Work-item construction

Each work item must be independently ownable and include:

- work-item ID and requirement/design references;
- exact owned files/modules or semantic boundary;
- inputs/dependencies that must already exist;
- required observable behavior;
- constraints and forbidden shortcuts;
- local verification commands;
- handoff artifact/commit expectations.

Use `assets/subagent-software-work-item.template.md` rather than giving a worker
a vague goal such as "port this area".

## Per-item workflow

1. **Implementer** reads the relevant contract, writes and runs the next
   behavioral test before its implementation when using TDD, makes it pass, and
   refactors under passing relevant checks. Return the change and actual
   evidence.
1. **Independent reviewer**, when justified, checks the diff against
   requirements and cited evidence. Use one proportionate pass; additional
   specialists need a distinct reason. A clean review is a valid outcome, not a
   staffing failure.
1. **Integrator** reconciles findings, applies authorized corrections, and
   reruns affected checks. The coordinator or original implementer may perform
   the correction; a separate agent is not mandatory merely because a role
   exists.
1. If evidence invalidates the design, stop dependent work and use change
   control. Do not silently change requirements or test expectations locally.
1. Consume each terminal result before releasing the worker; preserve the
   relevant evidence in the existing work record, not a new reporting framework.

## Forbidden progress hacks

Reject changes that make the work queue smaller without implementing the design:

- stubs, TODO-return values, `unimplemented!`, unconditional success paths;
- broad exception swallowing or `catch (...)` used to hide failures;
- disabling tests or assertions;
- replacing real behavior with mocks in production paths;
- mass `allow`, lint suppression, unsafe blocks, or type erasure without design
  authorization;
- compatibility aliases that silently drop unsupported fields;
- long comments that rationalize a workaround instead of correcting it.

## Phase completion check

Implementation is complete when all frozen work items are integrated into a
candidate that passes the implementation-level build/unit/static checks, all
blocking review findings are resolved, and every deviation from design has an
approved change request.
