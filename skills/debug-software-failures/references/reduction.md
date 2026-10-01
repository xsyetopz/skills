# Reduction, flaky failures, and packaging

Commands are POSIX sh; on Windows run them in Git Bash or WSL.

## Contents

- [Oracle polarity and strictness](#oracle-polarity-and-strictness)
- [Shrinking inputs](#shrinking-inputs)
- [Shrinking code and config](#shrinking-code-and-config)
- [Intermittent failures](#intermittent-failures)
- [Sanitizers and race detectors](#sanitizers-and-race-detectors)
- [Packaging a reproduction](#packaging-a-reproduction)

## Oracle polarity and strictness

The oracle reports only the reported failure (exact exception type and message prefix, exit status,
output value). Polarity differs per tool: `ddmin.py` counts `--fail-status` (default 1) as the
failure, `git bisect run` needs 0 for "no failure" and 1 for the failure, and a repro check often
exits 0 on reproduction. Invert or map the check, never the signature.

```python
result = subprocess.run([sys.executable, "repro.py"], capture_output=True,
                        text=True, check=False, timeout=10)
if result.returncode != 1 or "ValueError: too many values" not in result.stderr:
    raise SystemExit(f"wrong failure or unexpected success:\n{result.stderr}")
```

A loose oracle lets the reducer swap context for anything that prints the same message. Measured on
a 401-line CSV: `--fail-text 'expected 3 fields, got 4'` alone reduced to a stand-in header plus one
row (51 oracle runs); a wrapper that first returned "not the failure" unless the file started with
the real `id,name,city` header kept the real header (117 runs). If the minimal case shows a
different trigger, tighten the oracle and reduce again.

## Shrinking inputs

`scripts/ddmin.py` implements 1-minimal delta debugging ([Zeller and Hildebrandt 2002][ddmin-paper];
[Delta Debugging chapter][debuggingbook]):

```sh
python3 scripts/ddmin.py --fail-text 'expected 3 fields, got 4' \
  --output min.csv big.csv -- python3 parser.py {}
# stderr: units 401 -> 2, oracle runs 51
```

`--unit char` reduces characters. Re-run the oracle on `min.csv` alone. Line reduction of source
code yields mostly uncompilable candidates: use C-Vise (`cvise ./interesting.sh crash.c`, where the
script exits 0 on the bug) for C and C++, or put the compile step inside the oracle. The C-Vise
command follows its documented interestingness-script contract. Unverified by the authors.

## Shrinking code and config

Remove half of the remaining files, keys, dependencies, or flags, run the oracle, keep the half that
still fails, and repeat. A 40-key config needs about six runs to isolate one key. Log one line per
step, for example `removed [cache] section: python3 repro.py -> passes (keep it)`, so the reduction
replays from the original case.

## Intermittent failures

- Report failures/N for a fixed command, not "sometimes", and compare the same N before and after a
  fix. A lost-update race failed 0 of 200 runs by timing although the bug was real; 0 does not prove
  absence.
- Force the suspected interleaving with barriers so it fails every run: both threads read the old
  value, wait on a shared barrier, then both write. Do not turn the race into a different sequential
  failure.
- Pin variation: `env -i PATH="$PATH" TZ=UTC LC_ALL=C PYTHONHASHSEED=0 python3 repro.py`, plus
  injected clocks and recorded random seeds.
- When bisecting, convert the measured rate into a majority vote (see
  [bisect](bisect.md#flaky-and-performance-oracles)).

## Sanitizers and race detectors

- C/C++ corruption: `cc -g -fsanitize=address -fno-omit-frame-pointer x.c` (MSVC:
  `cl /fsanitize=address`) stops at the first invalid access with kind, size, and stacks
  ([AddressSanitizer][asan]). On one macOS setup the default SDK failed to link
  (`ld: tapi error: malformed file`); point `SDKROOT` at another installed SDK.
- `go test -race ./...` ([Go race detector][go-race]) and `-fsanitize=thread` for C/C++
  ([ThreadSanitizer][tsan]) name both racing stacks. They do not cover Python threads; force the
  interleaving instead.

## Packaging a reproduction

Use the smallest runnable form: one source file plus the exact command for C/C++, Rust (`rustc`, or
`Cargo.toml` only when features or resolution matter), JVM (`javac`, or a minimal Maven/Gradle
project for build behavior), and JS/TS/Bun (one file, plus manifest and lockfile when dependencies
matter). For a browser, give runnable HTML/CSS/JS with browser and version; for integrations, both
sides with minimal fixtures. Copy it to an empty directory and run it there. Use synthetic values
that keep the condition, never credentials or private data. The delivery record follows the [minimal
reproducible example][mre] fields: title, prerequisites, tested environment, run command, input,
expected, actual, verification command, and whether it is deterministic.

[ddmin-paper]: https://doi.org/10.1109/32.988498
[debuggingbook]: https://www.debuggingbook.org/html/DeltaDebugger.html
[asan]: https://clang.llvm.org/docs/AddressSanitizer.html
[go-race]: https://go.dev/doc/articles/race_detector
[tsan]: https://clang.llvm.org/docs/ThreadSanitizer.html
[mre]: https://stackoverflow.com/help/minimal-reproducible-example
