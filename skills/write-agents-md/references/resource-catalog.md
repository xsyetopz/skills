# Bundled resource catalog

Use this catalog to locate the exact skill-local files needed for the task. Do
not copy an asset unchanged unless its documented assumptions match the target
repository and organization controls.

| Path | Role and evidence boundary |
| --- | --- |
| `assets/AGENTS.template.md` | Output template for scoped repository instructions; replace every placeholder from inspected repository evidence. |

## Use rules

- `assets/` contains native templates and examples for agent inspection and
  adaptation. It does not override the target repository's established format.
- Replace placeholders and commands from inspected project evidence. Validate
  the resulting native file with repository and provider tooling.
- A parsed template proves syntax only; it does not prove hosted execution,
  permissions, secrets, approval gates, or deployment behavior.
