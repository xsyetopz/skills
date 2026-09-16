# Verification and evidence

Select evidence at the boundary of the claim. Run the smallest sufficient set
first, then broaden only when the change crosses another contract boundary.

| Claim | Sufficient evidence | Not sufficient by itself |
| --- | --- | --- |
| Configuration is syntactically valid | Provider parser/linter or accepted provider run for the exact file. | YAML parsing alone. |
| A trigger behaves as intended | Observed provider run/no-run for representative trusted and untrusted events, or authoritative event evaluation. | String inspection of the event name. |
| Secrets are protected | Effective permissions, event trust analysis, and run/log evidence showing no secret exposure. | Secret name absent from YAML text. |
| Artifact promoted is verified artifact | Digest/ID relationship from build through deploy and immutable provider behavior. | Matching filename. |
| Deployment works | Authorized deployment run and target-side observation/health check. | Successful build or dry-run alone. |

## Command patterns

```yaml
permissions:
  contents: read

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@<reviewed-commit>
        with:
          persist-credentials: false
      - run: ./scripts/ci-build.sh
      - uses: actions/upload-artifact@<reviewed-commit>
        with:
          name: app-${{ github.sha }}
          path: dist/
          if-no-files-found: error
```

Illustrative GitHub Actions shape. Use current reviewed action revisions and the
repository’s own script; do not copy placeholders unchanged.

```sh
# Prefer repository-provided validation, for example:
actionlint .github/workflows/*.yml
# GitLab: use CI Lint/API or project tooling.
# Bitbucket: use the provider validator or an isolated test branch.
```

Run only tools already approved or explicitly provisioned; record unavailable
provider checks.

## Result reporting

Separate authored checks, executed checks, static analysis, simulation,
integration/host execution, production observations, skipped checks, and
unavailable checks. Include relevant failure output. A green check establishes
only the properties it can discriminate; a single flaky pass, successful parser,
or valid configuration file is not broad runtime proof.
