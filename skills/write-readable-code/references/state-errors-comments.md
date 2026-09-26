# State, errors, comments, and tests

Cards that make data flow, side effects, and failure visible. Python
examples are in
[`state_errors.py`](../assets/examples/readable/python/state_errors.py);
the Go error example runs under
[`zen-of-python/verify.sh`](../assets/examples/zen-of-python/verify.sh).
Explicit defaults, deliberately silenced errors, and ambiguous input are
in [the Zen of Python cards](zen-of-python.md).

## Contents

- Explicit dependencies instead of ambient state
- Pure core, side effects at the edge
- Specific error handling with context
- Comments that state why
- Tests as executable documentation

## Explicit dependencies instead of ambient state

**Definition.** A function receives everything it reads (configuration,
clock, random source, services) as parameters or constructor arguments,
instead of reading globals, singletons, service locators, environment
variables, or the wall clock directly.

**Use when.**

- A function's result depends on `datetime.now()`, `os.environ`, a module
  global, or a static/singleton.
- A test needs monkeypatching or sleeping to control the function.

**Do not use when.**

- The value would pass through many layers to reach one leaf: inject it
  once at the composition root (the constructor of the object that needs
  it).

**Example.**

```python
def candidate_is_overdue(due: dt.date, today: dt.date, grace_days: int) -> bool:
    return today > due + dt.timedelta(days=grace_days)
```

replaces a version that read `dt.date.today()` and a module-level settings
dict.

**Cost removed.** Hidden inputs: the signature lists every input, and tests
pin `today` without patching.

**Verify.**

1. The oracle tests fixed dates at the grace boundary (day 3 not overdue,
   day 4 overdue) and matches the baseline on the real current date.
1. `rg -n 'datetime\.now|date\.today|time\.time\(|os\.environ' <changed files>`
   shows no new ambient reads in the core logic.

## Pure core, side effects at the edge

**Definition.** Separate computation (pure: output depends only on input,
no I/O) from effects (I/O, shared-state mutation); a thin effectful shell
calls the pure part.

**Use when.**

- One function both computes a result and writes it (file, network,
  database, logger).

**Do not use when.**

- The computation is trivial and the split adds a type passed only once.

**Example.**

```python
@dataclass(frozen=True)
class ScoreSummary:
    count: int
    average: float


def summarize(scores: list[int]) -> ScoreSummary:
    average = sum(scores) / len(scores) if scores else 0.0
    return ScoreSummary(count=len(scores), average=average)


def save_summary(summary: ScoreSummary, path: str) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(
            {"count": summary.count, "average": summary.average}, handle
        )
```

**Cost removed.** Tests of the computation need no filesystem, and readers
see where I/O happens.

**Verify.**

1. The oracle writes both versions to temporary files for `[]`, `[1, 2, 3]`,
   and `[10]` and compares the JSON.
1. The pure function has a unit test with no temporary files or mocks.

## Specific error handling with context

**Definition.** Catch only exceptions you can handle, at the level that can
handle them, and only around the operation that can fail. Translate
low-level errors into the caller's terms with context (file, key,
identifier) and chain the cause (`raise ... from error`, `Caused by`, `%w`,
`anyhow::Context`), so every failure either reaches a caller who can act
on it or is recorded with enough context to find it. This is the skill's
reading of PEP 20's "Errors should never pass silently".

**Use when.**

- Code catches a broad base type (`except Exception`, `catch (Exception)`,
  `catch (e)`), logs and continues, or returns a default on any failure.
- Code discards an error value (`_ =` in Go, `except: pass`).
- A `try` block spans more than the operation whose failure it
  translates.

**Do not use when.**

- The broad catch is the one deliberate top-level boundary (request
  handler, worker loop) that logs and reports; keep it there.
- An error is expected and ignored on purpose; see
  [unless explicitly silenced](zen-of-python.md#unless-explicitly-silenced).

**Example.** Python, with a documented default for the one expected case:

```python
def candidate_load_port(read_text: Callable[[str], str], path: str) -> int:
    try:
        document = json.loads(read_text(path))
    except FileNotFoundError:
        return 8080  # documented default when no config file exists
    except json.JSONDecodeError as error:
        raise ConfigError(f"{path}: invalid JSON: {error}") from error

    try:
        return int(document["port"])
    except (KeyError, TypeError, ValueError) as error:
        raise ConfigError(f"{path}: 'port' must be an integer") from error
```

Python translates only the lookup failure, so an error the renderer
raises keeps its identity
([`explicit_errors.py`][explicit-py]):

```python
def render_named(renderers, name, value):
    try:
        render = renderers[name]
    except KeyError as exc:
        raise ValueError(f"unknown renderer: {name}") from exc
    return render(value)
```

Go ([`errors/main.go`][errors-go]) wraps with `%w`, so callers can still
match the cause:

```go
func readLimit(path string) (int, error) {
    data, err := os.ReadFile(path)
    if err != nil {
        return 0, fmt.Errorf("read limit: %w", err)
    }
    limit, err := strconv.Atoi(string(data))
    if err != nil {
        return 0, fmt.Errorf("parse limit in %s: %w", path, err)
    }
    return limit, nil
}
```

The replaced Go version, `data, _ := os.ReadFile(path)`, returns 0 for
both a missing and a malformed file; the program asserts both.

**Cost removed.** Silent misconfiguration and failures that become
plausible values far from their cause: the `load_port` baseline returns
8080 for a missing file, invalid JSON, and a typo alike; the candidate
returns the default only for the documented case and otherwise names the
file and key. For the new Go version, `errors.Is(err, fs.ErrNotExist)` and
`errors.As(err, &numErr)` hold.
`test_same_oracle_accepts_implementation_and_rejects_exception_mutant`
rejects the Python mutant that wraps `render(value)` in the same `try`.

**Verify.**

1. The oracle feeds invalid JSON, a misspelled key, and a non-integer port:
   the baseline returns 8080 each time, the candidate raises `ConfigError`.
1. `python3 scripts/zen_scan.py <changed files>` reports no
   `silenced-except` or `broad-except`; `ruff check --select
   BLE,S110,S112` (Python) or the language's equivalent flags the same
   blind catches.
1. A test forces each failure and asserts its type or cause, not merely
   that "an error" occurred. Go: `go vet` passes, and a test uses
   `errors.Is` or `errors.As` on the returned error.

## Comments that state why

**Definition.** A comment states what the code cannot: a reason, a
constraint, a unit or external fact, a workaround's cause, or an invariant.
It never narrates the next line.

**Use when.**

- The code follows an external rule (protocol, hardware, legal), works
  around a bug (link the issue), or relies on an invariant a reader could
  break.
- You are about to write a comment longer than the code it describes:
  first try better names, structure, or types.

**Do not use when.**

- The comment restates the code (`# increment count`) or explains a
  confusing block that better names or structure would fix.

**Example.**

```c
/* Kernel reports this value in 512-byte sectors regardless of the
 * device's logical block size. */
uint64_t bytes = sectors * 512;
```

versus the narration to delete:

```python
count += 1  # increment count
```

A comment explaining a four-clause boolean is replaced by
[explaining variables](function-shape.md#explaining-variables)
(`candidate_can_retry` in `shape.py`). Not:

```python
def can_retry(status: int, attempt: int, elapsed_ms: int) -> bool:
    # Retry on 429 or any 5xx, while fewer than 5 attempts were made
    # and less than 30 seconds have passed.
    return (
        (status == 429 or 500 <= status < 600)
        and attempt < 5
        and elapsed_ms < 30_000
    )
```

**Cost removed.** Re-deriving facts that live outside the code, noise that
buries the comments that matter, and comments that drift from the code
they explain.

**Verify.**

1. Each comment added in the diff
   (`git diff -U0 <base> | rg '^\+\s*(#|//|/\*|\*)'`) states a reason or
   fact not visible in the code.

## Tests as executable documentation

**Definition.** Each test shows setup, action, and expected result in that
order, and its name states the behavior (`test_rejects_unpaid_orders`), so
a reader learns the contract without reading helpers.

**Use when.**

- Adding or changing behavior.

**Do not use when.**

- A generic helper would hide the input or the assertion: keep the values
  that matter in the test body.

**Example.**

```python
def test_specific_errors_replace_silent_default(self) -> None:
    def missing(_: str) -> str:
        raise FileNotFoundError

    self.assertEqual(se.candidate_load_port(missing, "c.json"), 8080)
```

**Cost removed.** Debugging the test harness to learn what is tested.

**Verify.**

1. Test names describe behavior (`rg -n 'def test_\w+' tests/` reads as a
   list of rules).
1. The test fails when you temporarily revert the change.

[explicit-py]: ../assets/examples/zen-of-python/python/explicit_errors.py
[errors-go]: ../assets/examples/zen-of-python/langs/go/errors/main.go
