# Operational decisions for Repository Agent Instructions

Use this guide after inspecting the request and target system for AGENTS.md
instructions. It selects an evidence path; it does not grant permission for an
external write or another consequential operation.

| Condition | Action | Do not substitute |
| --- | --- | --- |
| Rule applies to entire repository | Place once at root. | Copying into every subtree. |
| Subtree uses different build/test/generated rules | Add a nested file containing only differences and necessary local context. | A monolithic root essay. |
| Guidance is a reusable task workflow | Use/create an Agent Skill and link only if always relevant. | Embedding full skill body. |
| Rule is already enforced by obvious tooling | Include only if agent needs the invocation/path or common failure context. | Restating every lint rule. |
| Instruction depends on one temporary branch/task | Keep it in issue/plan/conversation, not durable AGENTS.md. | Committing transient status. |

## Unresolved decisions

A material scope, compatibility, interface, deployment, or policy choice for the
AGENTS.md instructions remains user-owned when repository evidence does not
settle it. Present concrete alternatives and consequences. Resolve routine
internal details that do not change an external contract.

## Avoiding false precision

Use thresholds, limits, versions, and acceptance criteria that govern the
AGENTS.md instructions. If none exists, report measurements or uncertainty. Do
not invent a timeout, reviewer count, confidence score, target, or error budget
and then treat it as a requirement.
