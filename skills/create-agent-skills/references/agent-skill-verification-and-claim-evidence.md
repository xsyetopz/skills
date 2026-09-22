# Verification and claim evidence for Agent Skill

Select evidence that can discriminate the claimed property of the Agent Skill
package. Run the smallest sufficient check first. Broaden only when another
contract boundary changed.

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
python3 scripts/validate_repository.py
python3 scripts/validate_assets.py

# Then validate one skill with the official/reference tool when available.
skills-ref validate skills/<skill-name>
```

Do not claim an unavailable tool passed. Structural validators do not replace
live task evaluation.

## Result reporting

For the Agent Skill package, separate authored checks, executed checks, static
analysis, simulation, host/integration execution, production observations,
skips, and unavailable checks. Include useful failure output. A green check
establishes only the property that it can discriminate.
