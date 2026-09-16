# Decision guide

Use this guide after inspecting the target repository and current request. It
selects an evidence path; it does not grant permission for writes or external
operations.

| Condition | Action | Do not substitute |
| --- | --- | --- |
| Rule applies to entire repository | Place once at root. | Copying into every subtree. |
| Subtree uses different build/test/generated rules | Add a nested file containing only differences and necessary local context. | A monolithic root essay. |
| Guidance is a reusable task workflow | Use/create an Agent Skill and link only if always relevant. | Embedding full skill body. |
| Rule is already enforced by obvious tooling | Include only if agent needs the invocation/path or common failure context. | Restating every lint rule. |
| Instruction depends on one temporary branch/task | Keep it in issue/plan/conversation, not durable AGENTS.md. | Committing transient status. |

## Unresolved decisions

A material product, compatibility, public-interface, deployment, or policy
choice remains user-owned when repository evidence does not settle it. Present
the concrete alternatives and consequences. Routine implementation details that
do not change an external contract remain the agent's responsibility.

## Avoiding false precision

Use project-defined thresholds, limits, versions, and acceptance criteria. When
none exists, report measurements or uncertainty; do not invent a timeout,
reviewer count, confidence score, supported version, performance target, or
error budget and then treat it as a requirement.
