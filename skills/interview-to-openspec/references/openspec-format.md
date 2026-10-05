# OpenSpec Change Format

Checked against OpenSpec 1.14.0 and its default `spec-driven` schema ([schema][schema],
[validator][validator], [concepts][concepts], [CLI][cli]). When the CLI is installed,
`openspec instructions <artifact> --change <name>` prints the project's own rules, which win over
this page.

## Contents

- [Layout and Names](#layout-and-names)
- [proposal.md](#proposalmd)
- [Spec Deltas](#spec-deltas)
- [design.md](#designmd)
- [tasks.md](#tasksmd)
- [Validation](#validation)
- [Commands](#commands)

## Layout and Names

```text
openspec/
├── config.yaml                 # schema, context, per-artifact rules
├── specs/<capability>/spec.md  # current behavior, the source of truth
└── changes/<change-name>/
    ├── .openspec.yaml          # schema, created; optional skip_specs, retire_capabilities
    ├── proposal.md
    ├── design.md               # only when needed
    ├── tasks.md
    └── specs/<capability>/spec.md   # deltas
```

- A change name is kebab-case: lowercase letters, digits, and single hyphens, with no hyphen at
  either end, at most 200 characters. Start it with a verb by convention: `add-team-accounts`.
- A capability names a durable behavior (`user-auth`), not this change's work
  (`add-login-endpoint`). Nested paths such as `identity/user-auth` are allowed; follow the
  project's existing layout. A modified capability uses its exact path from `openspec list --specs`.
- `openspec/project.md` and `openspec/AGENTS.md` are legacy files from older versions.
  `config.yaml` replaces them.

## proposal.md

```markdown
## Why

One or two sentences on the problem and why now (50 to 1,000 characters).

## What Changes

- Bullet list of changes. Mark a breaking change with **BREAKING**.

## Capabilities

### New Capabilities

- `team-accounts`: who belongs to a team and what members can see

### Modified Capabilities

- `user-auth`: login now selects a team

## Impact

Affected code, APIs, dependencies, and systems.
```

The validator requires `## Why` and `## What Changes`. Each capability listed needs a delta file.

## Spec Deltas

A delta file holds one or more of these sections, each with `### Requirement:` blocks:

- `## ADDED Requirements`: new behavior.
- `## MODIFIED Requirements`: changed behavior, with the whole updated block.
- `## REMOVED Requirements`: requirement names, each with `**Reason**` and `**Migration**`.
- `## RENAMED Requirements`: name changes only, as FROM and TO lines.

Requirement rules:

- The line after `### Requirement: <name>` holds the normative text with SHALL or MUST. A keyword
  only in the header does not count.
- Keep the text to 500 characters and one behavior; move examples and edge cases into scenarios.
- Every ADDED and MODIFIED requirement has at least one `#### Scenario:` with exactly four `#`.
  Three `#`, bullets, or a scenario inside a code fence are not counted.
- Scenario steps are bullets: `- **WHEN** ...`, `- **THEN** ...`, and `- **AND** ...`.

A delta for a new capability starts with `## Purpose` (50 or more characters); archive copies it
into the new main spec. A delta for an existing capability has no Purpose.

```markdown
## Purpose

Lets a group of users share projects under one billing account.

## ADDED Requirements

### Requirement: Team membership
The system SHALL let a team owner add an existing user to the team by email address.

#### Scenario: Owner adds a registered user
- **WHEN** the owner adds `ana@example.com`, who has an account
- **THEN** Ana is listed as a member of the team
- **AND** Ana sees the team's projects on her next request
```

### MODIFIED

1. Copy the whole block from `openspec/specs/<capability>/spec.md`, from `### Requirement:` through
   its last scenario, under `## MODIFIED Requirements`.
1. Keep the header text (whitespace is ignored) and every existing scenario header. Rewrite a
   scenario's steps to change its behavior; add new scenarios as needed.
1. A block that drops a scenario fails validation, because archive replaces the whole block.

Use ADDED, not MODIFIED, for a new concern that leaves existing behavior alone.

### REMOVED and RENAMED

```markdown
## REMOVED Requirements

### Requirement: Legacy export
**Reason**: Replaced by the v2 export endpoint.
**Migration**: Call `/api/v2/export` instead.

## RENAMED Requirements

- FROM: `### Requirement: Login`
- TO: `### Requirement: Password login`
```

- Each FROM line is followed immediately by its TO line.
- Archive applies RENAMED before MODIFIED, so a MODIFIED block for a renamed requirement uses the
  new name.
- A name may appear in only one of ADDED, MODIFIED, and REMOVED.
- Removing the last requirement of a capability deletes its spec file only when `.openspec.yaml`
  sets `retire_capabilities: true`.

### Changes without Deltas

A pure refactor, tooling, or docs change that changes no spec-level behavior sets
`skip_specs: true` in `.openspec.yaml` and has no `specs/` directory. Do not invent a requirement
to pass validation.

## design.md

Write it only for cross-cutting work, a new dependency or data model change, security, performance,
or migration risk, or ambiguity that needs a decision before coding. Sections:

- `## Context`: the current state and constraints; point to the proposal for motivation.
- `## Goals / Non-Goals`
- `## Decisions`: each choice with its reason and the alternatives considered.
- `## Risks / Trade-offs`: `[Risk] → Mitigation`.
- `## Migration Plan`: steps and rollback, when data or deployments change.
- `## Open Questions`: only unknowns that can be answered later without changing the specs, the
  approach, or the tasks. Resolve every other question with the user first.

## tasks.md

```markdown
# Tasks

## 1. Team model

- [ ] 1.1 Add the `teams` and `team_members` tables with a migration; verify with
  `just test tests/test_teams.py`
- [ ] 1.2 Add the owner-adds-member endpoint and its test; verify the test passes
```

- Each tracked task is `- [ ] X.Y description`. Only a box holding `x` counts as done, and a line
  without a checkbox is not tracked.
- Each task states how to verify it: a test, a command, an observable result, or a file.
- Order tasks by dependency. Each group ships its own tests and docs; do not collect them into a
  final group.

## Validation

`openspec validate <name> --strict --no-interactive` checks one change. `--strict` fails on warnings
too. `--json` prints a machine-readable report. Common messages and fixes:

| Message starts with | Fix |
| - | - |
| `Change must have at least one delta` | Add `specs/<capability>/spec.md`, or set `skip_specs: true` |
| `ADDED "X" must include at least one scenario` | Add a `#### Scenario:` block |
| `ADDED "X" should contain SHALL or MUST` | Put SHALL or MUST on the line after the header |
| `ADDED "X" is missing requirement text` | Add the normative line under the header |
| `MODIFIED "X" omits scenario(s)` | Copy the missing scenarios back into the block |
| `MODIFIED references old name from RENAMED` | Use the new name in the MODIFIED header |
| `Requirement present in both ...` | Keep each name in one operation only |
| `RENAMED FROM: "X" has no matching TO: line` | Put the TO line directly after FROM |
| `Why section must be at least 50 characters` | Expand `## Why` in proposal.md |
| `Purpose section is too brief` | Write 50 or more characters under `## Purpose` |
| `Requirement text is very long` | Split it, or move detail into scenarios |
| `Consider splitting changes with more than 10 deltas` | Split the change |

## Commands

| Command | Use |
| - | - |
| `openspec init --tools none` | Create `openspec/` without tool files; ask first |
| `openspec list --specs` | List capabilities and their paths |
| `openspec show <spec> --type spec --json --no-scenarios` | Read a spec's requirements briefly |
| `openspec new change <name>` | Create the change directory and `.openspec.yaml` |
| `openspec instructions <artifact> --change <name>` | Print the project's rules for one file |
| `openspec validate <name> --strict` | Check the change |
| `openspec archive <name> --yes` | Merge deltas into specs after implementation |

The default slash commands are `/opsx:propose`, `/opsx:explore`, `/opsx:apply`, `/opsx:update`,
`/opsx:sync`, and `/opsx:archive`. The legacy `/openspec:proposal` family was replaced. Install the
CLI with `bun add -g @fission-ai/openspec@latest` (Node.js 20.19 or later); ask the user first.

[schema]: https://github.com/Fission-AI/OpenSpec/blob/main/schemas/spec-driven/schema.yaml
[validator]: https://github.com/Fission-AI/OpenSpec/blob/main/src/core/validation/validator.ts
[concepts]: https://github.com/Fission-AI/OpenSpec/blob/main/docs/concepts.md
[cli]: https://github.com/Fission-AI/OpenSpec/blob/main/docs/cli.md
