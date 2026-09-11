---
name: review-software-security
description: >-
  Threat-model a software design, review code for exploitable trust-boundary
  failures, or verify security fixes. Use for defensive application and
  dependency security reviews, not routine feature work, compliance
  certification, incident response, or offensive testing of live systems.
---

# Review Software Security

Establish the authorized repository/design, deployed versions, entrypoints,
assets, actors, privileges, and review depth. Distinguish a design threat from
an observed implementation defect. Missing deployment facts are unknowns, not
proof that a control is absent. Do not turn a review into an unsolicited
rewrite.

Read only the relevant guidance:

- [Threat review and evidence](references/threat-review.md): model boundaries,
  prioritize reachable failures, and report findings with reproducible evidence.
- [Trust-boundary checks](references/trust-boundaries.md): authorization, input,
  identity, storage, network, and native-code hazards.
- [Supply chain and agent tools](references/supply-chain-and-agents.md):
  dependency identity, artifact provenance, secrets, and untrusted instructions.

Trace attacker-controlled input to a privileged operation and inspect
intervening controls in their actual configuration. Use current normative
specifications and official framework documentation matching the deployed
version. Prefer existing secure platform APIs and maintained libraries; do not
invent authentication, cryptography, parsers, or security-result formats.

Validate suspected defects with bounded, local, synthetic tests where practical.
Do not access other tenants, real secrets, production data, or third-party
targets to demonstrate impact. Network scanning, live exploitation, destructive
tests, and disclosure require separate scope and authorization.

Return prioritized findings with location, attacker capability, violated
control, impact, evidence, and a concrete repair/verification path. Identify
hypotheses and untested assumptions separately. No findings is not a security
certification. When repairs are requested, preserve legitimate behavior and
prove the vulnerable path fails without disabling security checks or hiding
diagnostics.
