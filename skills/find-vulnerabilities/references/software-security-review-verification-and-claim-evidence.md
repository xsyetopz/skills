# Verification and claim evidence for Software Security Review

Select evidence that can discriminate the claimed property of the security
finding. Run the smallest sufficient check first. Broaden only when another
contract boundary changed.

| Claim | Sufficient evidence | Not sufficient by itself |
| --- | --- | --- |
| Injection vulnerability | Attacker-controlled bytes reach an interpreter/query/template context without correct structural separation. | String concatenation found in unrelated path. |
| Authorization bypass | Unauthorized identity can perform/read the protected action/object under actual enforcement. | Button hidden or route name. |
| Path traversal | Controlled path escapes the allowed root after the application's normalization and access checks. | `..` appears in input. |
| Vulnerable dependency affects product | Resolved affected version, reachable used component, deployment preconditions, and advisory/source. | Package name in manifest. |
| Fix closes vulnerability | Negative exploit/regression case plus preserved legitimate behavior and relevant integration/control checks. | Input string blocked by one regex only. |

## Command patterns

Use the repository's existing commands. Record the exact command, working
directory, revision, configuration, and result.

## Result reporting

For the security finding, separate authored checks, executed checks, static
analysis, simulation, host/integration execution, production observations,
skips, and unavailable checks. Include useful failure output. A green check
establishes only the property that it can discriminate.
