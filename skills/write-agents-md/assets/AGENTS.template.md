# Repository agent instructions

## Scope

State which directory tree this file governs and which nested instruction files
may override it. Name the target agent clients only when their discovery or
precedence behavior differs.

## Source of truth

- Name handwritten source locations and generated outputs.
- Name the command that regenerates derived files.
- Do not hand-edit generated files unless the repository explicitly requires it.

## Commands

| Purpose | Working directory | Command | Evidence produced |
| --- | --- | --- | --- |
| Install/bootstrap | `<path>` | `<existing command>` | `<expected result>` |
| Focused test | `<path>` | `<existing command>` | `<expected result>` |
| Full validation | `<path>` | `<existing command>` | `<expected result>` |

## Change boundaries

- Preserve unrelated staged, unstaged, untracked, generated, and configuration
  state.
- Do not commit, publish, deploy, reset, or broaden compatibility unless the
  current request authorizes it.
- Follow repository ownership, security, and release controls.

## Required verification

Map each change category to the narrowest sufficient repository command. State
which host, service, device, or external environment is required for claims that
cannot be established locally.

## Delivery

Report files changed, commands actually run, observed results, skipped or
unavailable checks, and remaining evidence boundaries. Do not claim completion
from a narrower check than the requested result.
