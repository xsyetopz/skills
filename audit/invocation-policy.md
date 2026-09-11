# Invocation-policy decision

Decision updated 2026-09-12 after the user clarified the intended large-scale
usage: most skills must be manual; ordinary planning can remain implicit. This
supersedes the earlier decision to keep only two skills explicit-only. No
further policy clarification is required before completing GOAL.md.

## Current catalog policy

The current worktree contains 29 skills. Set
`policy.allow_implicit_invocation: false` for 27 skills. Only these two retain
implicit invocation:

- `design-software-boundaries`: ordinary architecture and boundary planning.
- `editor-extension-design`: editor-target selection and cross-editor planning.

Both still require a matching requested outcome, not a keyword. An editor name
in unrelated application work does not request extension planning.

All implementation, investigation, optimization, maintenance, formatting,
repository-operation, emulator-operation, and skill-authoring workflows are
manual. Their descriptions and bodies require explicit invocation by name. This
conservative catalog policy avoids unsolicited workflows for everyday users; it
is a user-selected product decision, not a portable format default.

`interrogate-plan` remains manual. Its sustained questioning mode differs from
ordinary planning and must not start merely because a user mentions a plan.
`format-github-markdown` also remains manual: editing Markdown does not
authorize adoption of its bundled formatting policy.

Invocation does not authorize every side effect. Existing approval requirements
and mutation boundaries still apply after a user selects a skill.

## Enforcement and evidence limits

The [Codex skills guide](https://learn.chatgpt.com/docs/build-skills) defines
the YAML field as a Codex invocation control. It is not part of the portable
[Agent Skills specification](https://agentskills.io/specification). Therefore
this repository cannot guarantee that every agent implementation enforces it.
The explicit description/body contract addresses agents that read instructions;
other clients need their own supported loading/invocation controls.

The earlier 38-package worktree passed official skills-ref and the bundled quick
validator. YAML assertions verify the then-current 36 false policies, the two
named implicit exceptions, and matching default-prompt names. Every manual
package states the invocation contract in its description and body. These are
static configuration and instruction checks, not universal runtime enforcement
tests.

Earlier catalog routing evaluations remain historical semantic-matching
observations. They do not demonstrate implicit activation under this new policy.
Pending domain packages carry the policy in the worktree but still require their
separate technical audits and integration before full-suite completion.

## Hosted-operation consolidation

The hosted issue, PR/MR, release, and settings candidates are now one manual
`manage-hosted-repositories` skill with conditional resource references. The
then-current worktree had 35 packages: 33 manual and the same two implicit
planning exceptions. The hosted package is integrated with source review and an
independent recovery scenario; this count alone does not certify API runtime
behavior.

## Emulator consolidation

Ten intermediate emulator packages became four: runtime operations and source
compilation for each emulator. All four remain explicit-only. Current metadata
checks establish 29 packages, 27 manual, and the same two implicit planning
exceptions. Helper and runtime-interface evidence is recorded separately in
[emulator evaluation](emulator-evaluation.md); package counts do not prove guest
execution or source-build success.
