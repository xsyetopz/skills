# Verification and evidence

Select evidence at the boundary of the claim. Run the smallest sufficient set
first, then broaden only when the change crosses another contract boundary.

| Claim | Sufficient evidence | Not sufficient by itself |
| --- | --- | --- |
| Skill is structurally valid | Official/repository validator plus link/path/schema checks. | File count or YAML parsing alone. |
| Description routes correctly | Repeated realistic positive, near-miss, and held-out activation observations. | Author intuition or keyword matching. |
| Skill improves task performance | With-skill versus baseline/prior-version tasks with inspectable artifacts and discriminating criteria. | One favorable example. |
| Script is reliable | Unit/integration tests for success, invalid input, missing dependency, and failure output. | Compiles or exits zero once. |
| Reference is sufficient | Agent completes representative task without inventing missing contracts; reviewer can trace decisions to source. | Long word count alone. |
| Package is scope-preserving | Original-versus-deliverable manifest/content/mode comparison at the authorized boundary. | A clean ZIP listing. |

## Command patterns

```sh
# Use repository-native validators first.
python scripts/validate_repository.py
python scripts/validate_assets.py

# Then validate one skill with the official/reference tool when available.
skills-ref validate skills/<skill-name>
```

Do not claim an unavailable tool passed. Structural validators do not replace
live task evaluation.

## Result reporting

Separate authored checks, executed checks, static analysis, simulation,
integration/host execution, production observations, skipped checks, and
unavailable checks. Include relevant failure output. A green check establishes
only the properties it can discriminate; a single flaky pass, successful parser,
or valid configuration file is not broad runtime proof.
