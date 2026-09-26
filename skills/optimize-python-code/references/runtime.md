# Runtime constructs

Interpreter behavior that code controls only indirectly: the specializing
adaptive interpreter, the experimental JIT, and import-time cost. Examples:
[`runtime.py`](../assets/examples/constructs/runtime.py),
[`startup_eager.py`](../assets/examples/constructs/startup_eager.py), and
[`startup_lazy.py`](../assets/examples/constructs/startup_lazy.py). The
free-threaded build is covered in
[concurrency](concurrency.md#threads-on-a-free-threaded-build), and the Linux
`perf` trampoline in
[measurement](measurement.md#linux-perf-trampoline).

State the exact patch version in any GC-sensitive claim. CPython 3.14.0–3.14.4
shipped an incremental cycle collector. 3.14.5 reverted it to the 3.13
generational collector after reports of memory pressure ([What's New
3.14][wn314-gc]). Local runs used 3.14.7. Tier: Executed for
specialization and deferred import; for the JIT, the status check is
executed and timing is not runnable here.

## Contents

- Specializing adaptive interpreter
- Experimental JIT
- Deferred import

## Specializing adaptive interpreter

**Definition.** Since 3.11 (PEP 659), CPython rewrites hot bytecode into
type-specialized instructions with inline caches, for example
`BINARY_OP_ADD_INT`, `LOAD_ATTR_INSTANCE_VALUE`, and `FOR_ITER_LIST`. It
de-specializes when the observed types change. What's New 3.11 reports a
1.25× average speedup on pyperformance over 3.10, and lists per-operation
gains of up to 10% for binary operations and up to 10–25% for subscripts
([What's New 3.11][wn311-spec], [PEP 659][pep659]).
`dis.get_instructions(f, adaptive=True)` (3.11+) shows the specialized forms,
and `Instruction.baseopname` (3.13+) the generic name ([dis][dis]).

**Use when.**

- A micro-optimization measured no gain. On 3.11+, global, attribute, and
  method loads are already cached, so manual hoisting saves less than on
  3.10.
- You write hot code: keep each site type-stable (same types at the same
  line, same attribute layout for all instances).

**Do not use when.**

- You would treat specialized opnames as a contract. Names and the set of
  specializations change between releases. Observed locally on 3.14: mixed
  `int + float` specialized as `BINARY_OP_EXTEND`, and an 8-class polymorphic
  attribute site still showed `LOAD_ATTR_INSTANCE_VALUE` after warmup. A
  specialized name does not prove the site is fast; measure with pyperf.
- No profile names the site: do not rewrite code to chase specializations.

**Example.**

```python
import dis


def add_ints(values):
    total = 0
    for value in values:
        total = total + value
    return total

for _ in range(100):
    add_ints(list(range(64)))
print([i.opname for i in dis.get_instructions(add_ints, adaptive=True)
       if i.opname != i.baseopname])
```

Measured output on 3.14.7: `['RESUME_CHECK', 'FOR_ITER_LIST',
'BINARY_OP_ADD_INT', 'JUMP_BACKWARD_NO_JIT']`. Before warmup, the list is
empty.

**Cost removed.** Generic dispatch at type-stable sites. The What's New 3.11
figures are upstream numbers; no local timing is claimed.

**Verify.**

1. `sh assets/examples/verify.sh verify` asserts that `BINARY_OP_ADD_INT`
   appears after warmup and prints `SPECIALIZED add_ints: [] -> [...]`.
1. For a project hot spot, compare pyperf results of type-stable and mixed
   inputs, and read `dis.get_instructions(f, adaptive=True)` after a warm
   run.

## Experimental JIT

**Definition.** CPython 3.13 added an experimental copy-and-patch JIT (PEP
744). It is compiled in with `--enable-experimental-jit` and switched at
start-up with `PYTHON_JIT=1`/`0`. 3.13 describes its gains as "modest"
([What's New 3.13][wn313-jit]). In 3.14, the official macOS and Windows
release binaries include it but leave it off. The docs say it "is not
recommended for production use" ([What's New 3.14][wn314-jit]).
`sys._jit.is_available()`, `is_enabled()`, and `is_active()` (3.14+) report
its state ([sys._jit][sys-jit]).

**Use when.**

- You experiment on a python.org 3.14 binary or a JIT-enabled build,
  comparing `PYTHON_JIT=0` and `PYTHON_JIT=1` with pyperf on the real
  workload.
- You audit a production interpreter: print `sys._jit.is_enabled()` to
  confirm the JIT is off.

**Do not use when.**

- The target is production. To leave experimental status, PEP 744 requires
  among other things an improvement "on the order of 5%" and a Steering
  Council decision ([PEP 744][pep744]).
- The interpreter lacks JIT support: `PYTHON_JIT=1` has no effect. The local
  Homebrew 3.14.7 build reports `is_available() == False`.
- You profile with the perf trampoline: stack trampolines "cannot be
  activated if the JIT is active" ([sys][sys-trampoline]).

**Example.**

```python
import sys

jit = getattr(sys, "_jit", None)  # 3.14+, CPython implementation detail
if jit is not None:
    print(jit.is_available(), jit.is_enabled())
```

```sh
PYTHON_JIT=0 python -m pyperf timeit --inherit-environ PYTHON_JIT \
  -o nojit.json -s 'from m import f' 'f()'
PYTHON_JIT=1 python -m pyperf timeit --inherit-environ PYTHON_JIT \
  -o jit.json -s 'from m import f' 'f()'
python -m pyperf compare_to nojit.json jit.json --table
```

pyperf 2.10.0 passes workers a reduced environment: `PATH`, `HOME`,
`PYTHONPATH`, `PYTHON_CPU_COUNT`, `PYTHON_GIL`, and a few others
([`_utils.create_environ`][pyperf-env]). Without `--inherit-environ
PYTHON_JIT`, workers never see the variable and both runs measure the same
configuration.

**Cost removed.** Not measured here.

**Verify.** Tier: status check executed; JIT timing not runnable here (no
JIT-capable interpreter).

1. `verify.sh verify` prints `JIT {'available': ..., 'enabled': ...}` and
   asserts that enabled implies available.
1. On a JIT-capable build, run the pyperf commands above. Draw no
   conclusion unless `compare_to` shows a significant row.

## Deferred import

**Definition.** Moving `import heavy` from module top level into the function
that needs it runs the import on the first call instead of at start-up. Later
calls find the module in `sys.modules`. `-X importtime` shows the cost that
moved ([cmdline][cmdline]).

**Use when.**

- `python -X importtime` shows a large cumulative time under a module that
  only some commands or code paths use (CLI subcommands, optional
  exporters).
- Start-up latency is the metric (CLI, serverless cold start, test
  collection).

**Do not use when.**

- The function is hot and the import sits inside its loop. Each call pays a
  `sys.modules` lookup; hoist it to function entry or keep it global.
- Import-time side effects must happen at start-up: plugin registration,
  monkeypatching, or configuration validation.
- Start-up must catch import errors. Deferred, a missing dependency fails at
  first use, in production. If you defer anyway, add a test that calls the
  deferred path.
- Type annotations need the name: guard the import with `TYPE_CHECKING` and
  use postponed annotations (`from __future__ import annotations`). A local
  `TYPE_CHECKING = False` avoids importing `typing` itself.

**Example.**

```python
from __future__ import annotations

TYPE_CHECKING = False
if TYPE_CHECKING:
    import decimal

def parse_price(text: str) -> decimal.Decimal:
    import decimal  # deferred; the first call pays the import once
    return decimal.Decimal(text).quantize(decimal.Decimal("0.01"))
```

**Cost removed.** Import work at start-up. Measured with `verify.sh verify`,
min of 5 warm runs with a bytecode cache: `startup_eager` 1,649 us and
`startup_lazy` 219 us cumulative (machine-specific). `decimal`, `numbers`, and
`_decimal` are no longer imported.

**Verify.**

1. `verify.sh verify` checks equal results for `"0"`, `"1.005"`, `"-2.5"`,
   and `"1e3"`, then asserts that `decimal` is absent from the lazy
   module's `-X importtime` output.
1. Run `python -X importtime -c 'import yourmodule' 2>&1 | tail -1`
   before and after; compare the minimum of several warm runs.

[cmdline]: https://docs.python.org/3/using/cmdline.html#cmdoption-X
[dis]: https://docs.python.org/3/library/dis.html#dis.get_instructions
[pep659]: https://peps.python.org/pep-0659/
[pep744]: https://peps.python.org/pep-0744/
[pyperf-env]:
  https://github.com/psf/pyperf/blob/2.10.0/pyperf/_utils.py
[sys-jit]: https://docs.python.org/3/library/sys.html#sys._jit
[sys-trampoline]:
  https://docs.python.org/3/library/sys.html#sys.activate_stack_trampoline
[wn311-spec]:
  https://docs.python.org/3/whatsnew/3.11.html#pep-659-specializing-adaptive-interpreter
[wn313-jit]:
  https://docs.python.org/3/whatsnew/3.13.html#an-experimental-just-in-time-jit-compiler
[wn314-gc]: https://docs.python.org/3/whatsnew/3.14.html#notable-changes-in-3-14-5
[wn314-jit]:
  https://docs.python.org/3/whatsnew/3.14.html#binary-releases-for-the-experimental-just-in-time-compiler
