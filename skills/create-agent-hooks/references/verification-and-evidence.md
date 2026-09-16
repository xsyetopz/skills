# Verification and evidence

Select evidence at the boundary of the claim. Run the smallest sufficient set
first, then broaden only when the change crosses another contract boundary.

| Claim | Sufficient evidence | Not sufficient by itself |
| --- | --- | --- |
| Handler logic works | Unit/fixture tests with exact documented payloads and expected result/exit code. | Source inspection alone. |
| Hook is registered | Host listing/diagnostic or observed invocation in the target scope. | Config file parses. |
| Hook blocks an action | A real or isolated host attempt is rejected by the documented mechanism. | Nonzero exit from a notification event. |
| Rollback is safe | Diff/removal test showing unrelated entries and files remain. | Deleting both old and new config files. |
| No secret leakage | Sanitized logs plus tests for redaction and argument handling. | No literal secret in one fixture. |

## Command patterns

```sh
python -m unittest scripts.test_assets
```

Validates the bundled fixtures and handlers. It does not prove that any
installed host loaded them.

## Result reporting

Separate authored checks, executed checks, static analysis, simulation,
integration/host execution, production observations, skipped checks, and
unavailable checks. Include relevant failure output. A green check establishes
only the properties it can discriminate; a single flaky pass, successful parser,
or valid configuration file is not broad runtime proof.
