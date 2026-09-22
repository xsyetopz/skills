# Verification and claim evidence for Agent Hook

Select evidence that can discriminate the claimed property of the agent hook.
Run the smallest sufficient check first. Broaden only when another contract
boundary changed.

| Claim | Sufficient evidence | Not sufficient by itself |
| --- | --- | --- |
| Handler logic works | Unit/fixture tests with exact documented payloads and expected result/exit code. | Source inspection alone. |
| Hook is registered | Host listing/diagnostic or observed invocation in the target scope. | Config file parses. |
| Hook blocks an action | A real or isolated host attempt is rejected by the documented mechanism. | Nonzero exit from a notification event. |
| Rollback is safe | Diff/removal test showing unrelated entries and files remain. | Deleting both old and new config files. |
| No secret leakage | Sanitized logs plus tests for redaction and argument handling. | No literal secret in one fixture. |

## Command patterns

```sh
python3 -m unittest scripts.test_assets
```

Validates the bundled fixtures and handlers. It does not prove that any
installed host loaded them.

## Result reporting

For the agent hook, separate authored checks, executed checks, static analysis,
simulation, host/integration execution, production observations, skips, and
unavailable checks. Include useful failure output. A green check establishes
only the property that it can discriminate.
