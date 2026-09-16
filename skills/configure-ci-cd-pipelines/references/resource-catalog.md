# Bundled resource catalog

Use this catalog to locate the exact skill-local files needed for the task. Do
not copy an asset unchanged unless its documented assumptions match the target
repository and organization controls.

| Path | Role and evidence boundary |
| --- | --- |
| `assets/github-actions/ci.reference.yml` | Provider-native reference pipeline. Inspect and replace every repository- or organization-specific value before use. |
| `assets/gitlab/ci.reference.yml` | Provider-native reference pipeline. Inspect and replace every repository- or organization-specific value before use. |
| `assets/bitbucket/bitbucket-pipelines.reference.yml` | Provider-native reference pipeline. Inspect and replace every repository- or organization-specific value before use. |

## Use rules

- `assets/` contains native templates and examples for agent inspection and
  adaptation. It does not override the target repository's established format.
- Replace placeholders and commands from inspected project evidence. Validate
  the resulting native file with repository and provider tooling.
- A parsed template proves syntax only; it does not prove hosted execution,
  permissions, secrets, approval gates, or deployment behavior.
