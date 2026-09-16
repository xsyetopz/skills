# Verification and evidence

Select evidence at the boundary of the claim. Run the smallest sufficient set
first, then broaden only when the change crosses another contract boundary.

| Claim | Sufficient evidence | Not sufficient by itself |
| --- | --- | --- |
| Emulator built | Native build command succeeds and expected executable/resources/package are inspected. | Configure step only. |
| Process launched | Exact command/process/log and isolated paths. | Argument builder output. |
| Guest booted | Observed guest state/serial/ELF execution in emulator. | Process window opened. |
| Guest defect reproduced | Exact target/scene/state and same defining failure. | Any crash. |
| Renderer issue isolated | Controlled backend/settings comparison with same guest state and host evidence. | Screenshot alone. |
| Source fix works | Bad/good reproduction plus relevant emulator tests/build and guest behavior. | Compilation only. |

## Command patterns

```sh
python -m unittest scripts.test_build_command
python scripts/build_command.py --help
```

The helper validates/constructs an argument vector. It does not launch the
emulator or establish guest behavior.

## Result reporting

Separate authored checks, executed checks, static analysis, simulation,
integration/host execution, production observations, skipped checks, and
unavailable checks. Include relevant failure output. A green check establishes
only the properties it can discriminate; a single flaky pass, successful parser,
or valid configuration file is not broad runtime proof.
