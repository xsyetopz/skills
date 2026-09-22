# Verification and claim evidence for Just Command Runner

Select evidence that can discriminate the claimed property of the justfile
recipe. Run the smallest sufficient check first. Broaden only when another
contract boundary changed.

| Claim | Sufficient evidence | Not sufficient by itself |
| --- | --- | --- |
| Justfile parses | `just --check` or supported parse/list command for installed version. | Text syntax highlighting. |
| Recipe runs correct command | Observed invocation/arguments/working directory and expected artifact. | Recipe body looks right. |
| Failures propagate | Known failing underlying command yields failing recipe with useful output. | Success path only. |
| Quoting is correct | Boundary tests with spaces/special characters and no unintended shell expansion. | Simple alphanumeric parameter. |
| Dependencies are correct | Observed execution order and no unintended reruns/side effects. | Recipe graph by inspection alone. |

## Command patterns

```sh
python3 -m unittest scripts.test_check_justfiles
python3 scripts/check_justfiles.py path/to/justfile
just --list
just --check
```

Use only options supported by the installed `just` version; unavailable `just`
means native execution is unverified.

## Result reporting

For the justfile recipe, separate authored checks, executed checks, static
analysis, simulation, host/integration execution, production observations,
skips, and unavailable checks. Include useful failure output. A green check
establishes only the property that it can discriminate.
