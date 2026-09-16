# Verification and evidence

Select evidence at the boundary of the claim. Run the smallest sufficient set
first, then broaden only when the change crosses another contract boundary.

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

Flags vary by Bun version and workflow. Use the target’s documented commands and
do not copy this block blindly.

## Result reporting

Separate authored checks, executed checks, static analysis, simulation,
integration/host execution, production observations, skipped checks, and
unavailable checks. Include relevant failure output. A green check establishes
only the properties it can discriminate; a single flaky pass, successful parser,
or valid configuration file is not broad runtime proof.
