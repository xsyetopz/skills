# Verification and evidence

Select evidence at the boundary of the claim. Run the smallest sufficient set
first, then broaden only when the change crosses another contract boundary.

| Claim | Sufficient evidence | Not sufficient by itself |
| --- | --- | --- |
| Justfile parses | `just --check` or supported parse/list command for installed version. | Text syntax highlighting. |
| Recipe runs correct command | Observed invocation/arguments/working directory and expected artifact. | Recipe body looks right. |
| Failures propagate | Known failing underlying command yields failing recipe with useful output. | Success path only. |
| Quoting is correct | Boundary tests with spaces/special characters and no unintended shell expansion. | Simple alphanumeric parameter. |
| Dependencies are correct | Observed execution order and no unintended reruns/side effects. | Recipe graph by inspection alone. |

## Command patterns

```sh
python -m unittest scripts.test_check_justfiles
python scripts/check_justfiles.py path/to/justfile
just --list
just --check
```

Use only options supported by the installed `just` version; unavailable `just`
means native execution is unverified.

## Result reporting

Separate authored checks, executed checks, static analysis, simulation,
integration/host execution, production observations, skipped checks, and
unavailable checks. Include relevant failure output. A green check establishes
only the properties it can discriminate; a single flaky pass, successful parser,
or valid configuration file is not broad runtime proof.
