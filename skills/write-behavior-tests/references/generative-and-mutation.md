# Generative, mutation, and instrumented testing

Techniques that find inputs or code changes that example tests miss.
[`assets/examples/verify.sh`][verify] runs each one:

- Hypothesis 6.168.1 runs in `network` mode, through `uv`.
- Go 1.27.1 fuzzing runs in `fuzz` mode.
- The bundled [`scripts/mutate.py`][mutate] and AddressSanitizer (Apple
  clang 21) run offline.

## Contents

- Property-based test
- Stateful model test
- Coverage-guided fuzzing and corpus regression
- Sanitizer run
- Mutation testing

## Property-based test

**Definition.** A test states a rule that must hold for every input
drawn from a strategy: an inverse, a conservation law, a count
relation, or agreement with a reference implementation. The library
generates inputs and, on failure, shrinks them to a minimal
counterexample ([Hypothesis][hypothesis]).

**Use when.**

- The contract has such a law.
- The input space is too large for hand-picked examples: text,
  sequences, nested data.

**Do not use when.**

- The only property you can state is "does not crash" for inputs that
  should be rejected.
- The property repeats the implementation. It then shares the
  implementation's mistakes, like a copied oracle.

Keep explicit examples for the important boundaries next to the
property.

**Example.** From [`props_examples.py`][props]:

```python
class SplitProperties(unittest.TestCase):
    @given(st.text(alphabet="ab:", max_size=12))
    def test_join_inverts_split(self, line):
        self.assertEqual(":".join(impl.split_fields(line)), line)

    @given(st.lists(st.text(alphabet="xy", max_size=3), min_size=1, max_size=5))
    def test_field_count_is_separators_plus_one(self, fields):
        line = ":".join(fields)
        self.assertEqual(len(impl.split_fields(line)), line.count(":") + 1)
```

The alphabet is narrowed to `ab:` so that separators appear often; a
default `st.text()` would rarely produce `::`.

**Cost removed.** Hand-picking inputs. Against `bug_split_drops_empty`,
Hypothesis failed both properties and shrank the counterexamples to
`line=':'` and `fields=['']`.

**Verify.**

1. `VARIANT=<mutant> uv run --no-project --with hypothesis==6.168.1
   python -m unittest props_examples` fails, and the log shows the
   shrunk `Falsifying example`.
1. Hypothesis reports no health-check failure from an over-filtered
   strategy.

## Stateful model test

**Definition.** Generate sequences of operations against the system
and a small independent model, and check an invariant after every step
(Hypothesis `RuleBasedStateMachine`). Preconditions restrict the
operations valid in each state.

**Use when.** Bugs depend on the order of operations: caches,
collections, protocol sessions, undo stacks.

**Do not use when.** The model would have to reimplement the system.
Compare against a reference implementation instead, or use
example-based [state transition tests][transitions].

**Example.**

```python
class CartMachine(RuleBasedStateMachine):
    def __init__(self) -> None:
        super().__init__()
        self.cart = impl.Cart()
        self.model: Counter[str] = Counter()

    @rule(item=st.sampled_from(["book", "pen"]))
    def add(self, item):
        self.cart.add(item)
        self.model[item] += 1

    @precondition(lambda self: sum(self.model.values()) > 0)
    @rule(data=st.data())
    def remove(self, data):
        item = data.draw(st.sampled_from(sorted(+self.model)))
        self.cart.remove(item)
        self.model[item] -= 1

    @invariant()
    def total_matches_model(self):
        expected = sum(impl.PRICES[i] * n for i, n in self.model.items())
        assert self.cart.total == expected, (self.cart.total, expected)
```

**Cost removed.** Writing order-dependent tests by hand. On
`bug_cart_remove_noop`, Hypothesis reported the shortest failing
sequence, `add(item='book')` then `remove(...)`, with
`AssertionError: (20, 0)`.

**Verify.**

1. The model uses no production code except shared constants such as
   `PRICES`.
1. A mutant that breaks one operation fails with a short printed step
   sequence.

## Coverage-guided fuzzing and corpus regression

**Definition.** A fuzzer mutates inputs to reach new code coverage and
reports any input that panics or fails a check. It saves failing
inputs as corpus files, which later plain test runs replay as
regression tests. Go has this built in ([Go fuzzing][gofuzz]); for C
and C++, [libFuzzer][libfuzzer] follows the same model.

**Use when.** Code parses or decodes untrusted or unstructured input:
file formats, protocols, escape sequences.

**Do not use when.**

- The input is a small closed set. List it instead.
- The target needs a network or live services. Make it hermetic first.

**Example.** [`escape_test.go`][escape]:

```go
func FuzzUnquote(f *testing.F) {
    for _, seed := range []string{"", "plain", `a\"b`, `\\`} {
        f.Add(seed)
    }
    f.Fuzz(func(t *testing.T, s string) {
        _, _ = Unquote(s) // any input: value or error, never a panic
        got, err := Unquote(Quote(s))
        if err != nil || got != s {
            t.Fatalf("Unquote(Quote(%q)) = %q, %v", s, got, err)
        }
    })
}
```

While this example was being written, the fuzzer found a real bug in
`Quote` in under a second: `Quote` ranged over runes, so the invalid
UTF-8 byte `\xa5` came back as U+FFFD. The fix iterates over bytes, and
the input is kept as `testdata/fuzz/FuzzUnquote/invalid-utf8`. The
second corpus entry, `trailing-backslash`, reproduces the bug that the
`bug` build tag restores.

**Cost removed.** Crashes on inputs nobody thought of. Measured: after
the fix, a 10-second run executed about 2.2 million inputs with no
failure. `go test -tags bug` replays the corpus and panics with
`index out of range`.

**Verify.**

1. `go test ./escape` replays the corpus without `-fuzz`, and CI runs
   it.
1. `go test -run '^$' -fuzz FuzzUnquote -fuzztime 10s ./escape` passes.
   Report the execution count.
1. Every crash found is saved in `testdata/fuzz/` and fixed. Never
   delete a crasher to make the run pass.

## Sanitizer run

**Definition.** Compiler instrumentation, such as AddressSanitizer
(ASan), UndefinedBehaviorSanitizer (UBSan), or ThreadSanitizer (TSan),
that checks memory, UB, or data races on the paths the program
executes ([AddressSanitizer][asan], [ThreadSanitizer][tsan]).

**Use when.** The code is C, C++, unsafe Rust, or a native extension.
Run its tests and fuzz targets under ASan and UBSan, and concurrent
code under TSan.

**Do not use when.**

- Measuring performance or allocation counts. The instrumentation
  changes both.
- Combining ASan with TSan in one build. They need separate builds.

**Example.** [`overflow.c`][overflow] writes one element past a
malloc'd array:

```c
static void fill(int *values, int count) {
    for (int i = 0; i <= count; i++) { /* bug: <= writes values[count] */
        values[i] = i;
    }
}
```

**Cost removed.** Memory errors that plain runs do not show. The plain
build printed `sum of first two: 1` and exited 0. The
`-fsanitize=address` build aborted with `heap-buffer-overflow`,
`WRITE of size 4`, and `in fill overflow.c:7`.

**Verify.**

1. The sanitizer build runs the same tests, and any report fails the
   run.
1. The report quotes the sanitizer's first frame with file and line.

## Mutation testing

**Definition.** A mutation tool makes small changes to the code (flips
a comparison, swaps an operator, changes a constant, replaces a return
value) and runs the tests after each one. A mutant the tests do not
detect "survives". A survivor means one of three things:

- a missing test;
- a weak assertion;
- an *equivalent* mutant, one that does not change behavior, which you
  justify rather than "fix".

Tools include [Stryker][stryker] for JS, TS, and C#, [mutmut][mutmut]
for Python, [cargo-mutants][cargo-mutants] for Rust, and [PIT][pit]
for Java. For Python, this skill bundles `scripts/mutate.py`, a stdlib
runner that mutates one file and works with any test command.

**Use when.**

- Checking whether the tests for a changed function catch plausible
  bugs.
- Finding which boundary is untested.

**Do not use when.** Chasing a mutation score across the whole
codebase. Target the changed functions (`--function`).

**Example.** Executed:

```text
$ python3 scripts/mutate.py subjects.py --function write_config \
    --test "python3 -m unittest -q weak_examples.WeakWriteConfig"
subjects.py:171: compare: NotIn -> In: killed
subjects.py:173: arith: Add -> Sub: survived
1 killed, 1 survived, 2 total
```

The survivor showed that no test covered a successful write. After
adding `test_valid_text_replaces_file_without_leftovers`, the same run
against `test_regressions` gives `2 killed, 0 survived`.

An equivalent mutant, from `test_mutate.py`: in `clamp(x, lo, hi)`,
changing `x < lo` to `x <= lo` survives every test, because at
`x == lo` both branches return the same value.

**Cost removed.** False confidence from coverage. `write_config` had
line coverage from the invalid-input test, but nothing checked the
success path. The survivor count measures this gap; it dropped from 1
to 0.

**Verify.**

1. `mutate.py` exits 0, or the report lists each survivor as missing
   test (then fixed), weak assertion (then fixed), or equivalent (with
   a reason).
1. The baseline passes before mutation; `mutate.py` refuses to run
   (exit 2) when it does not.

[verify]: ../assets/examples/verify.sh
[mutate]: ../scripts/mutate.py
[props]: ../assets/examples/behavior/props_examples.py
[escape]: ../assets/examples/go/escape/escape_test.go
[overflow]: ../assets/examples/c/overflow.c
[transitions]: inputs-and-oracles.md#state-transition-coverage
[hypothesis]: https://hypothesis.readthedocs.io/en/latest/
[gofuzz]: https://go.dev/doc/security/fuzz/
[libfuzzer]: https://llvm.org/docs/LibFuzzer.html
[asan]: https://clang.llvm.org/docs/AddressSanitizer.html
[tsan]: https://clang.llvm.org/docs/ThreadSanitizer.html
[stryker]: https://stryker-mutator.io/docs/mutation-testing-elements/mutant-states-and-metrics/
[mutmut]: https://mutmut.readthedocs.io/
[cargo-mutants]: https://mutants.rs/
[pit]: https://pitest.org/
