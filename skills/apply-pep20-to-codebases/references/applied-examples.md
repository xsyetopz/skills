# Python examples of cross-language design principles

The canonical executable examples are `assets/examples/explicit_behavior.py`.
Read them when changing defaults, exception translation, native options or file
ownership; run `python3 scripts/test_examples.py` from the skill root after
changing them. Python 3.10+ syntax is used. Do not raise the target project's
minimum version merely to reuse these examples.

| Decision | Explicit contract | Plausible but wrong shortcut |
| --- | --- | --- |
| Optional timeout | Only `None` selects the default; zero remains zero | `requested or default` |
| Missing catalog entry | Translate lookup failure; preserve the renderer's own error | A `try` around lookup and rendering together |
| Mapping option | Only an absent key selects the default; preserve a present value | Replace present `None`, false, zero, or empty with the default |
| Borrowed stream | Consume without closing caller-owned storage | Wrap a borrowed stream in unconditional close |
| Owned file | Keep the file open for the work and close on success/error | Return a lazy reader after leaving the file context |

Prefer a clear operation over a hierarchy that only renames it. A dataclass is
appropriate for named data with generated value behavior, not automatically for
every mapping. A protocol is justified by actual substitutable behavior, not the
possibility that an imaginary backend may appear later. Explicit does not mean
expanding a native API into a parallel wrapper with fewer controls.

Laziness changes evaluation timing, exceptions and resource retention. Preserve
those contracts before replacing a list with a generator. A specialized loop can
be the clearest implementation of a proven hot path; PEP 20 does not forbid
measured low-level code. Keep its invariant beside the unusual operation rather
than writing a commentary for every ordinary line.

PEP 20 is informational design guidance, not a linter, correctness proof or
universal performance policy. The tests establish specific behavior in the
examples, not compliance of an entire codebase with every aphorism.

Sources: [Python PEP 20][upstream-source-1], [errors][upstream-source-2],
[contextlib][upstream-source-3]

[upstream-source-1]: https://peps.python.org/pep-0020/
[upstream-source-2]: https://docs.python.org/3/tutorial/errors.html
[upstream-source-3]: https://docs.python.org/3/library/contextlib.html
