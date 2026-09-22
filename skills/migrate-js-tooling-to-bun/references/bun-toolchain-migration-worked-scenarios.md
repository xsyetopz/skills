# Worked scenarios for Bun Toolchain Migration

## Package manager only

Before:

```json
{
  "packageManager": "pnpm@10.0.0",
  "scripts": { "start": "node dist/server.js" }
}
```

After an authorized package-manager-only migration, `start` still uses Node.
Compare complete dependency graphs, workspace links, patches, peers, optional
packages, and registry behavior before removing the previous lockfile/tool
config.

## Test-runner contract

Create an inventory table:

| Behavior | Current runner | Bun candidate | Evidence |
| --- | --- | --- | --- |
| discovery patterns | exact config | exact Bun config | same intended files |
| per-test isolation | current semantics | observed semantics | state-leak test |
| snapshot format | current files | compatible/changed | reviewed diff |
| coverage thresholds | current config | supported mapping | failing threshold test |
| reporters/CI exit | current output | candidate output | CI consumer check |

## Dependency drift

If the candidate resolves a newer transitive version, do not call it equivalent.
Determine whether the old lock constraints, peer algorithm, platform package, or
registry metadata caused the difference. Either preserve the graph or obtain
authority for the dependency change and verify it separately.
