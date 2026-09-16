# Verification and evidence

Select evidence at the boundary of the claim. Run the smallest sufficient set
first, then broaden only when the change crosses another contract boundary.

| Claim | Sufficient evidence | Not sufficient by itself |
| --- | --- | --- |
| A refactor preserves behavior | Existing and added behavior checks over representative boundaries, plus public/type/serialization compatibility checks. | Similar-looking output on one example. |
| A name is better | Call sites become unambiguous about domain, units, ownership, or side effects and match project conventions. | Personal preference or shorter spelling. |
| An abstraction is unnecessary | No distinct invariant, lifecycle, substitution, or consumer remains after source/history analysis. | Only one current implementation. |
| A control-flow change is clearer | Fewer hidden states/paths with equivalent behavior and errors, supported by review and tests. | Lower line count alone. |
| A fallback can be removed | Consumer and support-policy evidence shows it was never required or is retired. | Age or empty local search alone. |

## Command patterns

```sh
python -m unittest scripts.test_examples
```

Runs the bundled example tests. It does not certify arbitrary codebases or other
languages.

## Result reporting

Separate authored checks, executed checks, static analysis, simulation,
integration/host execution, production observations, skipped checks, and
unavailable checks. Include relevant failure output. A green check establishes
only the properties it can discriminate; a single flaky pass, successful parser,
or valid configuration file is not broad runtime proof.
