# Operational decisions for Agent Skill

Use this guide after inspecting the request and target system for Agent Skill
package. It selects an evidence path; it does not grant permission for an
external write or another consequential operation.

| Condition | Action | Do not substitute |
| --- | --- | --- |
| A task is simple and the base agent already performs it reliably | Do not create a skill, or keep it self-contained and short if institutional policy is still needed. | A large generic workflow. |
| A workflow has distinct provider/language modes | Use one skill with explicitly gated references when the task intent is shared; split when triggers and execution differ. | Loading every mode or creating a router with no meaningful routing. |
| A mechanical transformation recurs | Bundle a tested script with clear inputs/output. | Ask the model to reimplement it each time. |
| A large example project is needed | Put the complete project under `assets/` and explain adaptation in a reference. | Scattered snippets that cannot build or run. |
| A skill is high risk or costly | Use realistic isolated forward evaluations and appropriate review. | Mandatory subagents for every small edit. |
| An optional OpenAI interface field is not requested/useful | Omit it. | Generated icons, colors, or license comments for completeness. |

## Unresolved decisions

A material scope, compatibility, interface, deployment, or policy choice for the
Agent Skill package remains user-owned when repository evidence does not settle
it. Present concrete alternatives and consequences. Resolve routine internal
details that do not change an external contract.

## Avoiding false precision

Use thresholds, limits, versions, and acceptance criteria that govern the Agent
Skill package. If none exists, report measurements or uncertainty. Do not invent
a timeout, reviewer count, confidence score, target, or error budget and then
treat it as a requirement.
