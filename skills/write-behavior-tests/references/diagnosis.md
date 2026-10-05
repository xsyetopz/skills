# Diagnosis and Instruments

Commands are POSIX sh; on Windows run them in Git Bash or WSL. `kill -QUIT`, `ulimit`, `lsof`, and
`/usr/bin/time` have no Windows form.

## Contents

- [Finding the Cause](#finding-the-cause)
- [Discriminating Experiments](#discriminating-experiments)
- [Differential Diagnosis](#differential-diagnosis)
- [Effective Settings](#effective-settings)
- [Wrong Output after a Long Pipeline](#wrong-output-after-a-long-pipeline)
- [Hangs](#hangs)
- [Native Crashes](#native-crashes)
- [Files, Network, Builds, Resources](#files-network-builds-resources)

## Finding the Cause

- Read the first error in the log, not the wrapper's summary line at the end:
  `grep -m1 -B2 -A8 '^error' run.log` (PowerShell:
  `sls -CaseSensitive '^error' run.log -Context 2,8 | select -First 1`).
- Change one thing per run, with a written prediction before it runs. A result that contradicts the
  prediction changes the hypothesis, not the expected result.
- Experiment, reduce, and bisect in a disposable copy or `git worktree add --detach ../REPO-wt REV`.
  Never undo experiments with `git checkout .`, `git reset --hard`, or `git stash` in a tree holding
  the user's work, because each also discards their changes. Remove the worktree and run
  `git bisect reset` at the end.
- Fix the cause, not the test or the symptom: no swallowed exceptions, longer timeouts, retries,
  deleted caches, random dependency upgrades, or edited expected output, unless the cause shows that
  is the correct fix. Put the fix at the component that owns the violated invariant, and show that
  removing only the cause removes the failure. Time or history correlation is not a cause.
- Report partial conclusions as partial ("reproduces only with these bytes on this revision")
  instead of inventing a cause.

## Discriminating Experiments

Pick an observation whose outcomes point to different hypotheses, and write the prediction first.

| Competing explanations | Discriminating observation | Misleading substitute |
| --- | --- | --- |
| Bad input vs parser regression | same bytes on good and bad revisions | retyping "equivalent" input |
| Allocation vs retention | allocation trace plus live-object retainers | one RSS reading |
| Deadlock vs slow I/O | thread stacks and wait graph with I/O state | raising the timeout |
| Race vs ordering bug | controlled schedule with barriers | sleeps and retries |
| Cache vs source error | named cold and warm runs | deleting every cache |
| Missing dependency vs code | the loader or import error of the real binary | bypassing initialization |

## Differential Diagnosis

Compare a working and a failing setup, then change one factor at a time toward the failing side
until the outcome flips, and confirm it flips back:

```sh
diff <(env | sort) failing-env.txt
diff <(python3 -m pip freeze) failing-freeze.txt
git diff good-sha bad-sha --stat
```

Use `$commit-and-rewrite-git` bisect for revisions and halving for config.

## Effective Settings

A limit that differs from the tool's documented default usually comes from a layer above it. Read
the effective value and its source before reporting a tool bug:

```sh
env | rg -i 'limit|max|concurren'
git config --list --show-origin | rg -i hookspath
python3 -m pip config debug
```

Report the value, the file or variable that sets it, and the documented default.

## Wrong Output after a Long Pipeline

Check state at the midpoint (log, assert an invariant, or break in a debugger) and continue in the
half where it first goes wrong. The defect sits in the stage between the last correct and the first
wrong value.

## Hangs

- Python: `faulthandler.dump_traceback_later(2.0, exit=True)` dumps every thread's stack and exits;
  `python3 -X faulthandler` also dumps on fatal signals ([faulthandler][faulthandler]). It shows
  nothing for native code that holds the GIL.
- Go: a full deadlock prints `fatal error: all goroutines are asleep - deadlock!`; a partial one is
  not detected, so send `kill -QUIT pid` (`GOTRACEBACK=all` for detail) ([runtime][go-runtime]).
- JVM: `jcmd "$pid" Thread.print > threads.txt`, then
  `grep -A20 'Found one Java-level deadlock' threads.txt` ([jcmd][jcmd]). For an exited process use
  `-XX:+HeapDumpOnOutOfMemoryError` or JFR.

## Native Crashes

`lldb --batch -o run -k bt -k quit -- ./prog` runs the program and prints the stop reason and stack
only if it crashes ([lldb][lldb]). Build with `-g -O0`. Without `-k quit`, batch mode waited on the
stopped process with one lldb install. For timing-dependent crashes use core dumps or
[sanitizers](generative.md#sanitizers).

## Files, Network, Builds, Resources

- Vague "cannot open" or permission errors:
  `strace -f -e trace=openat,connect ./app 2>&1 | grep -E 'ENOENT|ECONNREFUSED'` on Linux. macOS has
  no `strace`, and `dtruss` cannot trace system binaries under SIP; use application logging.
- Build fails with a summary only, or on some machines: use `cargo build -v`, `make V=1`,
  `cmake --build . --verbose`, `dotnet build -v detailed`, or `go build -x`, and build in a fresh
  `git worktree add /tmp/clean HEAD` to separate cache from source problems. Name the stale cache;
  do not just delete it.
- Fails after running a while (`EMFILE`, out-of-memory kills): `ulimit -a`, `lsof -p "$pid" | wc -l`
  (Windows: `(Get-Process -Id PID).HandleCount`), and `/usr/bin/time -l` (macOS) or `-v` (Linux).
  Find the leak before raising a limit.

[faulthandler]: https://docs.python.org/3/library/faulthandler.html
[go-runtime]: https://pkg.go.dev/runtime
[jcmd]: https://docs.oracle.com/en/java/javase/25/docs/specs/man/jcmd.html
[lldb]: https://lldb.llvm.org/man/lldb.html
