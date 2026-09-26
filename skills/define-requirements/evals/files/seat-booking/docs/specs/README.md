# Specifications

Each feature spec in this directory uses the same line format so specs can
be linted and traced from tests.

- A requirement is one list item: `REQ-<AREA>-<NNN> [source: <where it came
  from>] <sentence>`. The sentence is one EARS-style statement with exactly
  one `shall`.
- An acceptance criterion is one list item: `AC-<AREA>-<NNN> verifies
  REQ-<AREA>-<NNN>: Given ..., when ..., then ...`.
- An open question is one list item: `DEC-<AREA>-<NNN>: <question>`.

See `login-lockout.md` for a complete spec.
