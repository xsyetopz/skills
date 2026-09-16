# Finding: [specific violated trust boundary]

Location: exact path/symbol or provider configuration and revision.
Preconditions: attacker-controlled input, attacker authority and required state.
Trace: entry point → validation/authorization → sensitive operation.
Observation: demonstrated effect, or the precise unverified step in the path.
Impact: affected confidentiality, integrity or availability under those
preconditions. Correction: the smallest change that restores the boundary, with
native controls. Verification: regression input and expected
rejection/containment; legitimate input that must continue to work. Do not
substitute a scanner label for this evidence.
