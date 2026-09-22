# Verification and claim evidence for Bun Toolchain Migration

Select evidence that can discriminate the claimed property of the Bun migration.
Run the smallest sufficient check first. Broaden only when another contract
boundary changed.

| Claim | Sufficient evidence | Not sufficient by itself |
| --- | --- | --- |
| Install migration equivalent | Resolved graph/workspace links and lifecycle outcomes match authorized expectations. | `bun install` exit 0. |
| Tests migrated | Same intended suite/cases, fixtures, snapshots, coverage/reporting, exit behavior, and relevant platform behavior. | Some tests pass. |
| Build output compatible | Artifact contents, entry points, source maps, module formats, assets, and downstream consumer checks. | Bundle file exists. |
| Runtime retained | Deployment/container/process commands and integration tests still invoke intended runtime. | Local dev command. |
| Performance improved | Matched repeated measurements of the selected responsibility under controlled conditions. | Bun marketing or one run. |

## Command patterns

```sh
bun --version
bun install --frozen-lockfile
bun test
# Run the repository's existing type/build/integration commands separately.
```

Flags vary by Bun version and workflow. Use the target's documented commands and
do not copy this block blindly.

## Result reporting

For the Bun migration, separate authored checks, executed checks, static
analysis, simulation, host/integration execution, production observations,
skips, and unavailable checks. Include useful failure output. A green check
establishes only the property that it can discriminate.
