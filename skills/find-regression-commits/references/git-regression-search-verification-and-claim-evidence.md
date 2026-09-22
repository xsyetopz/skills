# Verification and claim evidence for Git Regression Search

Select evidence that can discriminate the claimed property of the regression
search. Run the smallest sufficient check first. Broaden only when another
contract boundary changed.

| Claim | Sufficient evidence | Not sufficient by itself |
| --- | --- | --- |
| Boundary is good/bad | Same oracle observed expected classification on exact revisions. | Release notes or dates. |
| Commit introduced defect | Parent good, commit bad with same signature and relevant diff. | Bisect output alone. |
| Revision is untestable | Recorded setup/tool/dependency failure distinct from defect. | Any nonzero exit. |
| Result is unique | Bisect result without unresolved skip ambiguity and manual confirmation. | One candidate shown. |
| Cleanup preserved user state | Status/worktree comparison before and after. | No visible files in current directory. |

## Command patterns

```sh
python3 scripts/bisect_oracle.py --help
python3 -m unittest scripts.test_bisect_oracle scripts.test_bisect_integration
```

Tests the wrapper and disposable-history behavior; it does not locate a defect
in the target repository.

## Result reporting

For the regression search, separate authored checks, executed checks, static
analysis, simulation, host/integration execution, production observations,
skips, and unavailable checks. Include useful failure output. A green check
establishes only the property that it can discriminate.
