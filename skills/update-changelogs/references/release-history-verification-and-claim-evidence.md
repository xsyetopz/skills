# Verification and claim evidence for Release History

Select evidence that can discriminate the claimed property of the changelog
entry. Run the smallest sufficient check first. Broaden only when another
contract boundary changed.

| Claim | Sufficient evidence | Not sufficient by itself |
| --- | --- | --- |
| Entry belongs in range | Diff/merge/revision identity and actual behavior. | Commit subject only. |
| Change is user-visible | Affected supported interface/workflow/output and evidence. | Large code diff. |
| Breaking classification | Established supported contract and incompatible effect. | Renamed internal symbol. |
| Release is published | Provider/package registry/tag state and artifact identity. | Version heading exists. |
| Version syntax valid | SemVer/project policy parser plus authorized chosen version. | Regex alone decides significance. |

## Command patterns

```sh
python3 -m unittest scripts.test_validators
python3 scripts/audit_changelog.py CHANGELOG.md
python3 scripts/audit_semver.py 1.2.3
```

Use the repository's actual paths and policies. Passing these scripts does not
choose a release version or prove publication.

## Result reporting

For the changelog entry, separate authored checks, executed checks, static
analysis, simulation, host/integration execution, production observations,
skips, and unavailable checks. Include useful failure output. A green check
establishes only the property that it can discriminate.
