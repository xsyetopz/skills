# Verification and claim evidence for Cross Language PEP 20

Select evidence that can discriminate the claimed property of the cross-language
design review. Run the smallest sufficient check first. Broaden only when
another contract boundary changed.

| Claim | Sufficient evidence | Not sufficient by itself |
| --- | --- | --- |
| A refactor preserves behavior | Existing and added behavior checks over representative boundaries, plus public/type/serialization compatibility checks. | Similar-looking output on one example. |
| A name is better | Call sites become unambiguous about domain, units, ownership, or side effects and match project conventions. | Personal preference or shorter spelling. |
| An abstraction is unnecessary | No distinct invariant, lifecycle, substitution, or consumer remains after source/history analysis. | Only one current implementation. |
| A control-flow change is clearer | Fewer hidden states/paths with equivalent behavior and errors, supported by review and tests. | Lower line count alone. |
| A fallback can be removed | Consumer and support-policy evidence shows it was never required or is retired. | Age or empty local search alone. |

## Command patterns

```sh
python3 -m unittest scripts.test_examples
```

Runs the bundled example tests. It does not certify arbitrary codebases or other
languages.

## Result reporting

For the cross-language design review, separate authored checks, executed checks,
static analysis, simulation, host/integration execution, production
observations, skips, and unavailable checks. Include useful failure output. A
green check establishes only the property that it can discriminate.
