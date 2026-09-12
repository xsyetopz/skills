---
name: interrogate-plan
description: >-
  Interrogate a supplied plan, design, or requirements set until contradictions,
  assumptions, unresolved decisions, and material risks are explicit. Activate
  only when invoked as $interrogate-plan; do not implement the plan or choose
  answers for the user.
---

# Interrogate Plan

Run this workflow only when the user explicitly invokes this skill by name. A
mention of its subject in another task is not an invocation.

Question the artifact rather than improving or implementing it.

Start from its stated goals, constraints, actors, interfaces, states, failure
modes, rollout, and success evidence. Ask the smallest high-value batch of
concrete questions. Follow each answer to its consequences, expose
contradictions and hidden assumptions, and distinguish decisions from facts that
can be verified.

Do not invent missing decisions, argue for novelty, or turn preferences into
requirements. Stop when remaining unknowns are either resolved, explicitly
accepted as risks, assigned to an owner, or identified as external facts to
verify. Return a compact decision log containing resolved choices, open
questions, assumptions, contradictions, risks, and acceptance criteria.
