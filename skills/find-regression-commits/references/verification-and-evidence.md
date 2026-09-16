# Verification and evidence

Select evidence at the boundary of the claim. Run the smallest sufficient set
first, then broaden only when the change crosses another contract boundary.

| Claim | Sufficient evidence | Not sufficient by itself |
| --- | --- | --- |
| Boundary is good/bad | Same oracle observed expected classification on exact revisions. | Release notes or dates. |
| Commit introduced defect | Parent good, commit bad with same signature and relevant diff. | Bisect output alone. |
| Revision is untestable | Recorded setup/tool/dependency failure distinct from defect. | Any nonzero exit. |
| Result is unique | Bisect result without unresolved skip ambiguity and manual confirmation. | One candidate shown. |
| Cleanup preserved user state | Status/worktree comparison before and after. | No visible files in current directory. |

## Command patterns

```sh
python scripts/bisect_oracle.py --help
python -m unittest scripts.test_bisect_oracle scripts.test_bisect_integration
```

Tests the wrapper and disposable-history behavior; it does not locate a defect
in the target repository.

## Result reporting

Separate authored checks, executed checks, static analysis, simulation,
integration/host execution, production observations, skipped checks, and
unavailable checks. Include relevant failure output. A green check establishes
only the properties it can discriminate; a single flaky pass, successful parser,
or valid configuration file is not broad runtime proof.
