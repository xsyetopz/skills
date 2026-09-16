# Verification and evidence

Select evidence at the boundary of the claim. Run the smallest sufficient set
first, then broaden only when the change crosses another contract boundary.

| Claim | Sufficient evidence | Not sufficient by itself |
| --- | --- | --- |
| Injection vulnerability | Attacker-controlled bytes reach an interpreter/query/template context without correct structural separation. | String concatenation found in unrelated path. |
| Authorization bypass | Unauthorized identity can perform/read the protected action/object under actual enforcement. | Button hidden or route name. |
| Path traversal | Controlled path escapes the allowed root after the application’s normalization and access checks. | `..` appears in input. |
| Vulnerable dependency affects product | Resolved affected version, reachable used component, deployment preconditions, and advisory/source. | Package name in manifest. |
| Fix closes vulnerability | Negative exploit/regression case plus preserved legitimate behavior and relevant integration/control checks. | Input string blocked by one regex only. |

## Command patterns

Use the repository’s existing commands. Record the exact command, working
directory, revision, configuration, and result.

## Result reporting

Separate authored checks, executed checks, static analysis, simulation,
integration/host execution, production observations, skipped checks, and
unavailable checks. Include relevant failure output. A green check establishes
only the properties it can discriminate; a single flaky pass, successful parser,
or valid configuration file is not broad runtime proof.
