# Verification and evidence

Select evidence at the boundary of the claim. Run the smallest sufficient set
first, then broaden only when the change crosses another contract boundary.

| Claim | Sufficient evidence | Not sufficient by itself |
| --- | --- | --- |
| Entry belongs in range | Diff/merge/revision identity and actual behavior. | Commit subject only. |
| Change is user-visible | Affected supported interface/workflow/output and evidence. | Large code diff. |
| Breaking classification | Established supported contract and incompatible effect. | Renamed internal symbol. |
| Release is published | Provider/package registry/tag state and artifact identity. | Version heading exists. |
| Version syntax valid | SemVer/project policy parser plus authorized chosen version. | Regex alone decides significance. |

## Command patterns

```sh
python -m unittest scripts.test_validators
python scripts/audit_changelog.py CHANGELOG.md
python scripts/audit_semver.py 1.2.3
```

Use the repository’s actual paths and policies. Passing these scripts does not
choose a release version or prove publication.

## Result reporting

Separate authored checks, executed checks, static analysis, simulation,
integration/host execution, production observations, skipped checks, and
unavailable checks. Include relevant failure output. A green check establishes
only the properties it can discriminate; a single flaky pass, successful parser,
or valid configuration file is not broad runtime proof.
