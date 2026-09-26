# Oracle and reduction

Shrinking a reported failure to the smallest input and program that still
fail the same way. Examples are in
[`assets/examples/reproduce/`](../assets/examples/reproduce/verify.sh);
`verify.sh` runs each
one (executed locally, macOS arm64).

## Contents

- Failure oracle
- Oracle strictness
- Delta debugging with ddmin
- Manual halving of code, config, and dependencies
- Reduction log
- Language-specific reducers

## Failure oracle

**Definition.** A command that exits 0 only when the specific reported
failure occurs: the exact exception type and message prefix, exit status,
output value, or HTTP response. Setup errors, timeouts, and different
crashes are not the failure.

**Use when.** Always, before editing anything; the oracle judges every
reduction step.

**Do not use when.** The oracle would accept any non-zero exit; a missing
file or an import error would then look like the failure.

**Example.**

```python
result = subprocess.run(
    [sys.executable, str(reproducer)],
    capture_output=True, text=True, check=False, timeout=10,
)
if (
    result.returncode != 1
    or "ValueError: too many values to unpack" not in result.stderr
):
    raise SystemExit(f"wrong failure or unexpected success:\n{result.stderr}")
```

Runnable: `assets/examples/reproduce/python-delimiter-repro/verify.py`.

One signature serves every tool, but the exit polarity differs: a
reproduction check such as `verify.py` exits 0 when the failure
reproduces, `ddmin.py` counts `--fail-status` (default 1) as the failure,
and `git bisect run` needs 0 for "no failure" and 1 for the failure
([bisect oracles](bisect-oracles.md#exit-code-mapping-oracle)). Invert or
map the check, never the signature.

**Cost removed.** Reductions that drift to a different failure.

**Verify.**

1. The oracle passes on the original case; break the case (fix the bug by
   hand) and the oracle fails.

## Oracle strictness

**Definition.** How much of the original context the oracle requires. A
loose oracle checks only the error text, so a reducer may replace context
with anything that triggers the same message. A strict oracle also
requires the context that makes the failure meaningful.

**Use when.** The failure depends on structure (a header, a schema, a
configuration section) that a reducer could remove or substitute.

**Do not use when.** The context is irrelevant; a loose oracle finds
smaller cases faster.

**Example.** On a 401-line CSV, `ddmin` with only
`--fail-text 'expected 3 fields, got 4'` produced 2 lines: row 286 as a
stand-in header and the quoted-comma row 287 (51 oracle runs). A wrapper
that also requires the real `id,name,city` header produced the header and
row 287 (117 oracle runs). The strict wrapper and its run, from
`assets/examples/reproduce/verify.sh`:

```sh
cat >"$WORK/strict.py" <<PY
import subprocess, sys
text = open(sys.argv[1]).read()
if not text.startswith("id,name,city\\n"):
    sys.exit(0)  # not the failure we are reducing
sys.exit(subprocess.run([sys.executable, "$ROOT/csv-reduction/parser.py",
                         sys.argv[1]]).returncode)
PY
"$PY" "$DDMIN" "$WORK/big.csv" --oracle "$PY $WORK/strict.py {}" \
    --output "$WORK/strict.csv"
```

Measured strict result:

```text
id,name,city
287,"Smith, Jr.",city0
```

**Cost removed.** Minimal cases that mislead the reader about the trigger.

**Verify.**

1. `verify.sh` runs both oracles and checks the first line of the strict
   result is the real header.

## Delta debugging with ddmin

**Definition.** `ddmin` repeatedly splits the failing input into n chunks
and keeps any chunk or complement that still fails, increasing n when
nothing fails, until the result is 1-minimal: removing any single unit
makes the failure disappear ([Zeller and Hildebrandt 2002][ddmin-paper];
[Delta Debugging chapter][debuggingbook]).

**Use when.** A large input file (data, source, config, log) triggers the
failure.

**Do not use when.** The failure depends on timing or on the input's size
(a buffer that overflows only above N bytes); the reducer removes what
matters.

**Example.**

```sh
python3 scripts/ddmin.py big.csv \
  --oracle 'python3 parser.py {}' \
  --fail-text 'expected 3 fields, got 4' --output min.csv
# stderr: units 401 -> 2, oracle runs 51
```

`--unit char` reduces characters instead of lines.

**Cost removed.** Hours of manual trimming; each oracle run is counted.

**Verify.**

1. `python3 scripts/test_ddmin.py` checks 1-minimality.
1. The reduced file fails the oracle on its own:
   `python3 parser.py min.csv`.

## Manual halving of code, config, and dependencies

**Definition.** Remove half of the remaining candidates (source files,
configuration keys, dependencies, feature flags), run the oracle, keep the
half that still fails, and repeat.

**Use when.** The candidates cannot be expressed as lines of one file
(project structure, build options).

**Do not use when.** Removing a candidate breaks the build; remove only
what the build tolerates.

**Example.** A 40-key config reproduces a startup crash; removing keys
21-40 keeps the crash, removing 11-20 of the rest does not, so the
trigger is in 11-20; four more halvings isolate one key. The same loop,
with a stand-in oracle instead of starting the program:

```python
config = {f"key{i:02}": "on" for i in range(1, 41)}


def crashes(cfg):  # oracle: stands in for "start the app with cfg"
    return "key11" in cfg


keep = dict(config)
candidates = sorted(config)
while len(candidates) > 1:
    half = (len(candidates) + 1) // 2
    first, second = candidates[:half], candidates[half:]
    trial = {k: v for k, v in keep.items() if k not in second}
    if crashes(trial):
        keep, candidates = trial, first
        print(f"removed {second[0]}-{second[-1]}: crash kept")
    else:
        candidates = second
        print(f"removed {second[0]}-{second[-1]}: no crash")
print("trigger:", candidates[0])
```

Measured output, which is the reduction log:

```text
removed key21-key40: crash kept
removed key11-key20: no crash
removed key16-key20: crash kept
removed key14-key15: crash kept
removed key13-key13: crash kept
removed key12-key12: crash kept
trigger: key11
```

**Cost removed.** Irrelevant configuration in bug reports.

**Verify.**

1. The reduction log records each removal and the oracle result.

## Reduction log

**Definition.** One line per removal step: what was removed, the command,
and whether the same failure remained.

**Use when.** Any manual reduction longer than a few steps.

**Do not use when.** An automated reducer already reports its runs.

**Example.**

```text
removed tests/ fixtures      python3 repro.py -> same ValueError
removed [cache] section       python3 repro.py -> passes (keep it)
removed requests dependency   python3 repro.py -> same ValueError
```

**Cost removed.** Repeating steps after a mistake.

**Verify.**

1. Replaying the log from the original case ends at the final case.

## Language-specific reducers

**Definition.** Tools that reduce source programs while keeping them
compilable: C-Reduce and C-Vise for C and C++, and Hypothesis's
shrinking for property-based tests in Python.

**Use when.** The input is a program and line-based ddmin produces too many
uncompilable candidates.

**Do not use when.** The tool is not installed and the program is small;
`ddmin.py` with a compile step in the oracle works.

**Example.**

```sh
cvise ./interesting.sh crash.c   # interesting.sh exits 0 on the bug
```

Unverified: C-Vise and Hypothesis are not installed on the authoring
machine. The command follows C-Vise's documented use of an
"interestingness" script, which plays the oracle's role.

**Cost removed.** Wasted oracle runs on syntax errors.

**Verify.**

1. The interestingness script is the oracle used for the original report.

[ddmin-paper]: https://doi.org/10.1109/32.988498
[debuggingbook]: https://www.debuggingbook.org/html/DeltaDebugger.html
