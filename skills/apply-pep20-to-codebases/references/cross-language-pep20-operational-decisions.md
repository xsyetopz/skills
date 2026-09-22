# Operational decisions for Cross Language PEP 20

Use this guide after inspecting the request and target system for cross-language
design review. It selects an evidence path; it does not grant permission for an
external write or another consequential operation.

| Condition | Action | Do not substitute |
| --- | --- | --- |
| The code is readable but uses a language-native idiom unfamiliar to the reviewer | Keep the idiom and document only if the project audience needs it. | Rewriting it into Python-shaped code. |
| Multiple mechanisms implement the same policy without distinct consumers | Choose one canonical path and migrate authorized callers. | Adding a façade that preserves all duplication. |
| A long function reflects one coherent algorithm with explicit stages | Extract only stages with stable names/contracts or keep it together. | Mechanical extraction into tiny functions with no semantic boundary. |
| A public name is ambiguous | Rename only with authority and a compatibility/migration decision. | Creating permanent aliases for imagined consumers. |
| Error handling is implicit or swallowed | Use the language's normal typed/result/exception mechanism and preserve context. | Returning default success values or catch-all fallback behavior. |

## Unresolved decisions

A material scope, compatibility, interface, deployment, or policy choice for the
cross-language design review remains user-owned when repository evidence does
not settle it. Present concrete alternatives and consequences. Resolve routine
internal details that do not change an external contract.

## Avoiding false precision

Use thresholds, limits, versions, and acceptance criteria that govern the
cross-language design review. If none exists, report measurements or
uncertainty. Do not invent a timeout, reviewer count, confidence score, target,
or error budget and then treat it as a requirement.
