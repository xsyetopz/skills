# Worked scenarios for Repository Agent Instructions

## Root instructions

```markdown
# Repository instructions

- Run commands from the repository root.
- Use `just test-unit <package>` for a changed package.
- Run `just validate` before delivery.
- Edit schemas under `schema/`.
- Files under `generated/` are produced by `just generate`; do not edit them by
  hand.
- Preserve user changes in the Git index and working tree.
- Do not commit unless requested.
- For database migrations, read `docs/migrations.md` and use the existing
  migration tool.
```

Each rule is project-specific and points to the canonical mechanism.

## Nested instructions

`services/payments/AGENTS.md` should contain only payment-specific differences,
for example the local integration command, external sandbox requirement, and
restricted fixture path. It should not repeat the root Git and formatting rules.

## Wrong category

A ten-step procedure for writing a VS Code extension belongs in an on-demand
skill. A current branch checklist belongs in the task plan. Credentials belong
in a secret manager. AGENTS.md should not become all three.
