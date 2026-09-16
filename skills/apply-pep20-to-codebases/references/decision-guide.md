# Decision guide

Use this guide after inspecting the target repository and current request. It
selects an evidence path; it does not grant permission for writes or external
operations.

| Condition | Action | Do not substitute |
| --- | --- | --- |
| The code is readable but uses a language-native idiom unfamiliar to the reviewer | Keep the idiom and document only if the project audience needs it. | Rewriting it into Python-shaped code. |
| Multiple mechanisms implement the same policy without distinct consumers | Choose one canonical path and migrate authorized callers. | Adding a façade that preserves all duplication. |
| A long function reflects one coherent algorithm with explicit stages | Extract only stages with stable names/contracts or keep it together. | Mechanical extraction into tiny functions with no semantic boundary. |
| A public name is ambiguous | Rename only with authority and a compatibility/migration decision. | Creating permanent aliases for imagined consumers. |
| Error handling is implicit or swallowed | Use the language’s normal typed/result/exception mechanism and preserve context. | Returning default success values or catch-all fallback behavior. |

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
