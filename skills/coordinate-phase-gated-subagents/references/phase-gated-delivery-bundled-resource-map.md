# Bundled resource map for Phase Gated Delivery

Use this map to locate resources for multi-agent phase coordination. Load only
the item required by the current decision. When an example is a native project,
preserve its manifest, lockfile, descriptors, fixtures, and relative layout.

| Path | Role and evidence boundary |
| --- | --- |
| `assets/software-baseline-change-request.template.md` | Output template; copy and adapt without treating placeholders as facts. |
| `assets/software-defect-review.template.md` | Output template; copy and adapt without treating placeholders as facts. |
| `assets/software-design-baseline.template.md` | Output template; copy and adapt without treating placeholders as facts. |
| `assets/software-phase-completion.template.md` | Output template; copy and adapt without treating placeholders as facts. |
| `assets/software-requirement-verification.template.md` | Output template; copy and adapt without treating placeholders as facts. |
| `assets/software-requirements-baseline.template.md` | Output template; copy and adapt without treating placeholders as facts. |
| `assets/subagent-software-work-item.template.md` | Output template; copy and adapt without treating placeholders as facts. |

## Use rules

- Use a script only for its documented multi-agent phase coordination
  transformation. Inspect arguments, stdout, stderr, exit status, and created
  files.
- Assets contain multi-agent phase coordination templates, fixtures, or complete
  example projects. Preserve required manifests and relative paths when copying
  them.
- A deliberately faulty fixture demonstrates fault discrimination; it is not a
  production recommendation.
- A passing bundled example establishes only its own contract in the executed
  environment; it does not prove the target system.
