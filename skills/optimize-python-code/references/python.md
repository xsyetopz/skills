# Python performance

Record implementation/version, build mode, packages, workload, and whether a
free-threaded CPython build is in use. Do not assume all Python execution is
CPython or that the GIL state follows only from the version number; extension
compatibility can affect free-threaded execution.

Use the existing workload and profiler first. `cProfile` attributes Python call
execution; native-library work and waiting need appropriate complementary
evidence. `tracemalloc` traces Python-managed allocations when enabled; it is
not total process RSS or a complete view of native allocations. Start tracing
early enough to capture the allocations being investigated.

Use `pyperf` for repeatable isolated comparisons when available rather than one
noisy wall-clock run. Preserve interpreter options, warmup, data distribution,
imports/setup placement, and result consumption. Measure algorithmic changes
over input sizes that expose the actual scaling, not only a tiny constant case.

Prefer reducing repeated work, choosing a fitting container, and using
implemented-in-native-code operations when they preserve the contract and
measurement supports them. A comprehension, generator, or eager list has
different allocation, laziness, and exception timing; choose according to the
caller, not a universal speed ranking.

Threads can overlap suitable I/O; CPU parallelism depends on the implementation,
GIL state, extension behavior, and workload. Processes incur serialization and
lifecycle costs. Free-threaded built-in container implementation details are not
a substitute for the program's own synchronization invariants. Async code does
not make CPU-bound Python work parallel by itself.

Bound caches and define invalidation only when a cache is justified. Preserve
resource lifetime when streaming; a lazy iterator can outlive an open file or
retain its input. Do not remove validation or change numerical precision merely
to improve a benchmark unless the behavior change is explicitly authorized.

Sources: [Python profiling][python-profiling], [tracemalloc][ref-tracemalloc],
[free-threading HOWTO][free-threading-howto],
[pyperf](https://pyperf.readthedocs.io/en/latest/).

## Executable fixtures

Requires Python 3.10 or newer and POSIX `sh` for the convenience runner.

Read [the fixture execution contract][ref-the-fixture-execution-contract] before
running these examples. It defines disposal, supported modes, same-check
defective/corrected implementation checks, and the distinction between
correctness and timing.

From the skill root:

```sh
sh assets/examples/verify.sh
sh assets/examples/verify.sh correctness 1
```

The complete project and its native configuration are in [the python
assets](../assets/examples). Copy that directory intact when adapting a fixture.
Run only this language; the target project keeps its own toolchain.

### Semantic regression cases

Source: [semantics.py][ref-semantics-py].

| Case | Required contract |
| --- | --- |
| 1 | Independent mutable defaults |
| 2 | One-shot iterator reuse |
| 3 | Duplicate preservation |
| 4 | First occurrence on a maximum tie |
| 5 | Accurate summation versus explicit float regrouping |
| 6 | KeyboardInterrupt must not be swallowed |
| 7 | Cancellation propagates through an awaited task |
| 8 | Independent nested containers |

## Baseline and candidate

Use [the comparison sources](../assets/examples/comparisons) and their
expected-result checks. The [shared contract](executable-fixtures.md) explains
input-domain limits and why these programs are not speed claims.

## Benchmark fixture

Copy [the python asset directory](../assets/examples) intact. Run the following
commands in its `benchmarks/` subdirectory.

Copy the entire Python asset directory. Provision Python and `pyperf==2.10.0` in
the selected environment (or use a PEP 723 runner explicitly permitted to
resolve the inline dependency). Installation is not part of `verify.sh`.

From this directory, after `sh ../verify.sh comparisons` passes:

```sh
python bench_pyperf.py --variant baseline --rigorous -o baseline.json
python bench_pyperf.py --variant candidate --rigorous -o candidate.json
python -m pyperf compare_to baseline.json candidate.json --table
python -m pyperf stats baseline.json
python -m pyperf stats candidate.json
```

Benchmark names are identical across variants; worker processes receive the
variant explicitly. Fixture creation and equivalence checks are outside timing.
Function execution and its returned result construction are inside timing. The
selected cases do not mutate their caller-owned inputs. Native pyperf options,
including affinity, processes, warmups, tracking and timeouts, remain available.
Run allocation tracking separately from wall-time measurement. Repeat baseline
and candidate order to inspect drift. The illustrative sizes are not a
production workload. Do not suppress instability warnings or infer tail latency
from a function microbenchmark. This optional dependency was not available
during the repository's offline validation.

Sources: [source][source] and [source][source-2]

## Failure reproduction

Source: [the isolated reproducer][ref-the-isolated-reproducer]. From the skill
root, run `sh assets/examples/verify.sh reproduction`. Direct commands below
assume a clean copy of the reproduction directory.

Expected: both returned lists contain `[1, 2]`.

Actual: the second list is empty because the iterator is exhausted.

From a clean copy, run `python3 repro.py`. Exit zero means the documented
mismatch was reproduced; it does not mean the implementation is correct.

[python-profiling]: https://docs.python.org/3/library/profile.html
[free-threading-howto]: https://docs.python.org/3/howto/free-threading-python.html
[source]: https://pyperf.readthedocs.io/en/latest/api.html
[source-2]: https://pyperf.readthedocs.io/en/latest/runner.html

[ref-tracemalloc]: https://docs.python.org/3/library/tracemalloc.html
[ref-the-fixture-execution-contract]: executable-fixtures.md
[ref-semantics-py]: ../assets/examples/correctness/semantics.py
[ref-the-isolated-reproducer]: ../assets/examples/reproduction
