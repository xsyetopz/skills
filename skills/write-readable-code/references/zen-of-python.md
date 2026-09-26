# Zen of Python (PEP 20)

The 19 aphorisms of [PEP 20][pep20] used as design questions for code in
any language. PEP 20 states only the 19 lines. The readings, conditions,
and checks below are this skill's policy, not text of the PEP: present
them as this skill's reading, and never claim that a codebase "complies
with PEP 20". Headings quote the aphorism. Apply each card in the target
language's idiom (Go `%w`, Rust `ErrorKind`, TypeScript `??`, Java static
methods, C guard clauses); do not port Python syntax.

Every example runs in
[`zen-of-python/verify.sh`][verify] (Python 3.14.7, Node 26.8.2, Go 1.27.1,
rustc 1.98.1; macOS arm64). Python code can be scanned first with
`python3 scripts/zen_scan.py PATH`, which reports `silenced-except`,
`broad-except`, `wide-suppress`, `or-default`, and `star-import`.

## Contents

- Aphorism map
- Explicit is better than implicit
- Simple is better than complex
- Complex is better than complicated
- Readability counts
- Special cases aren't special enough to break the rules
- Although practicality beats purity
- Unless explicitly silenced
- Refuse the temptation to guess
- There should be one obvious way to do it
- Now is better than never
- Although never is often better than right now
- If the implementation is hard to explain
- Namespaces are one honking great idea

## Aphorism map

Each line of PEP 20, this skill's reading of it, and the card that
applies it. Aphorisms that share a construct with another readability
card live in that card.

| # | Aphorism | This skill's reading | Card |
| --- | --- | --- | --- |
| 1 | Beautiful is better than ugly. | Changed lines match the project's formatter; nothing else is reformatted | [Unrequested churn][churn] |
| 2 | Explicit is better than implicit. | Only a missing value selects a default; effects and ownership are visible | [Explicit](#explicit-is-better-than-implicit) |
| 3 | Simple is better than complex. | No abstraction with one implementation | [Simple](#simple-is-better-than-complex) |
| 4 | Complex is better than complicated. | One named home for a repeated policy | [Complex](#complex-is-better-than-complicated) |
| 5 | Flat is better than nested. | Guard clauses before the main work | [Guard clauses][guard] |
| 6 | Sparse is better than dense. | One decision per line | [Lookup table][sparse] |
| 7 | Readability counts. | Names state the contract | [Readability](#readability-counts) |
| 8 | Special cases aren't special enough to break the rules. | No branch the general rule already covers | [Special cases](#special-cases-arent-special-enough-to-break-the-rules) |
| 9 | Although practicality beats purity. | A measured, local, tested exception | [Practicality](#although-practicality-beats-purity) |
| 10 | Errors should never pass silently. | Narrow catches that keep the cause | [Specific errors][errors] |
| 11 | Unless explicitly silenced. | One named error, one operation, one reason | [Explicitly silenced](#unless-explicitly-silenced) |
| 12 | In the face of ambiguity, refuse the temptation to guess. | Fail on ambiguous input; verify external facts | [Refuse to guess](#refuse-the-temptation-to-guess) |
| 13 | There should be one-- and preferably only one --obvious way to do it. | One entry point per operation | [One obvious way](#there-should-be-one-obvious-way-to-do-it) |
| 14 | Although that way may not be obvious at first unless you're Dutch. | Document the canonical way instead of adding a second | [One obvious way](#there-should-be-one-obvious-way-to-do-it) |
| 15 | Now is better than never. | Deprecate with a warning now | [Now](#now-is-better-than-never) |
| 16 | Although never is often better than *right* now. | No public surface before a caller | [Never](#although-never-is-often-better-than-right-now) |
| 17 | If the implementation is hard to explain, it's a bad idea. | A why-comment each test can check | [Hard to explain](#if-the-implementation-is-hard-to-explain) |
| 18 | If the implementation is easy to explain, it may be a good idea. | Necessary, not sufficient | [Hard to explain](#if-the-implementation-is-hard-to-explain) |
| 19 | Namespaces are one honking great idea -- let's do more of those! | Qualified names, no star imports | [Namespaces](#namespaces-are-one-honking-great-idea) |

## Explicit is better than implicit

**Definition.** The code shows which inputs select a default, which
effects happen, and who owns a resource. The most common implicit rule
is a truthiness default: `value or default` in Python and
`value || default` in JavaScript treat `0`, `""`, and `False` as
missing. Hidden inputs such as the clock or globals are covered by
[explicit dependencies][ambient].

**Use when.**

- A parameter or option has a valid falsy value, such as a timeout of
  0, an empty prefix, or `retries: 0`.
- A function borrows a stream or file that its caller must close.
- A wrapper hides options of the native API it wraps.

**Do not use when.**

- The language idiom is already explicit, such as Go zero values
  documented as meaningful, or Rust's `Option::unwrap_or`.
- Spelling out every argument at each call site would only repeat a
  documented default.

**Example.** Python ([`explicit_errors.py`][explicit-py]):

```python
_MISSING = object()


def effective_timeout(value: float | None, default: float) -> float:
    """Only None means unspecified. Zero remains an explicit value."""
    return default if value is None else value


def option(options: Mapping[str, object], name: str, default: object) -> object:
    """Missing key uses the default; present None, False, 0, and '' survive."""
    value = options.get(name, _MISSING)
    return default if value is _MISSING else value
```

TypeScript ([`explicit.ts`][explicit-ts]), where `??` replaces only
`null` and `undefined`:

```ts
export function effectiveRetries(options: RetryOptions): number {
  return options.retries ?? 3;
}
// options.retries || 3 turns { retries: 0 } into 3
```

**Cost removed.** Wrong values for valid input, such as a timeout of 0
becoming 30 seconds. The mutant `value or default` fails
`effective_timeout(0, 10) == 0`, and `zen_scan.py` counts
`or-default` findings, which drop to 0.

**Verify.**

1. `python3 scripts/zen_scan.py src` reports no `or-default` in the
   changed functions.
1. A test passes the falsy value (0, `""`, `False`) and asserts it
   survives; the same test fails on the `or` mutant.
1. TypeScript: `node explicit.ts` prints
   `retries 0 kept with ??; || turned it into 3`.

## Simple is better than complex

**Definition.** Use the fewest parts that meet today's requirements. An
interface, factory, or strategy earns its place only with at least two
implementations or a caller that substitutes one. Extracting a layer
because code looks similar or "might" vary is over-abstraction, a common
agent failure.

**Use when.**

- An abstraction has one implementation and one caller, or exists only
  for an unrequested "future backend".
- You are about to add an interface with one implementation or a
  configuration option nobody sets. For a one-caller function that only
  renames syntax, see [when not to extract][extract].

**Do not use when.**

- A second implementation exists, including a test double that a test
  actually substitutes.
- The abstraction is a published extension point that callers outside
  the repository implement.
- The name documents a domain rule.

**Example.** Java. The replaced design
([`SimpleBefore.java`][java-before]) has an interface, an
implementation, and a factory for one formatting rule. The new design
([`SimpleAfter.java`][java-after]):

```java
public static String formatPrice(long cents, String currency) {
    String symbol = SYMBOLS.get(currency);
    if (symbol == null) {
        throw new IllegalArgumentException("unknown currency " + currency);
    }
    return String.format("%s%d.%02d", symbol, cents / 100, cents % 100);
}
```

The Python pair in [`structure.py`][structure-py] and
[`structure_before.py`][before-py] shows the same change. Likewise, an
`IRetryStrategy` with one `DefaultRetryStrategy` and a factory becomes one
`retry(call, attempts=3)` function until a second strategy is required.

**Cost removed.** Types and indirection every reader must trace to find
the real code. Measured: `javac` emits 4 class files for the old design
and 1 for the new, with identical output for all 10 inputs.

**Verify.**

1. An equivalence test runs old and new on the same inputs; keep it
   until the old code is deleted.
1. Count types before and after: class files, `go doc -short` entries,
   or `rg -c '^(class|interface) '`.
1. For each new interface or abstract class, count implementations with
   `rg -n 'implements IName|: IName\b|impl Name for'`; one implementation
   needs a stated reason.
1. `rg` for the removed type names finds no remaining use.

## Complex is better than complicated

**Definition.** Keep a problem's real complexity in one named place
with a stated contract and its own tests. Complicated code spreads the
same policy over many call sites in slightly different forms.

**Use when.** The same policy appears in several places: retry,
backoff, pagination, locking order, or unit conversion.

**Do not use when.** The call sites differ in ways the policy must keep
separate, such as error types or deadlines; merging them would add
parameters that only one caller uses each.

**Example.** Go ([`retry/main.go`][retry-go]):

```go
// Retry calls op until it succeeds, returns a non-transient error, runs
// out of delays, or ctx ends. It waits delays[i] after failure i.
func Retry(ctx context.Context, delays []time.Duration, op func() error) error {
    for attempt := 0; ; attempt++ {
        err := op()
        done := err == nil || !errors.Is(err, errTransient)
        if done || attempt == len(delays) {
            return err
        }
        select {
        case <-ctx.Done():
            return errors.Join(err, ctx.Err())
        case <-time.After(delays[attempt]):
        }
    }
}
```

The Python `retry()` in `structure.py` also takes a `sleep` function,
so tests run without waiting.

**Cost removed.** Call sites each getting a policy detail wrong, such as
retrying a permanent error or ignoring cancellation. The program checks
4 policy cases in one place: success on the third try, giving up, no
retry for a permanent error, and stopping on cancel.

**Verify.**

1. `rg -n 'time.Sleep|time.sleep' src` finds no hand-written retry loop
   outside the helper.
1. The helper's tests cover each clause of its doc comment.

## Readability counts

**Definition.** Names and signatures tell the reader what a call does,
what it changes, and in which units. The name states the operation the
contract performs, not a nearby one.

**Use when.** A name hides a distinction that callers rely on, as in
the table below.

| Unclear name | Name that states the contract |
| --- | --- |
| `process` | `parse_frame`, `validate_checksum`, `publish` |
| `cancel` | `request_cancel` (returns at once), `wait_stopped` |
| `timeout` (unit unknown) | `timeout_s`, or a `Duration` type ([units][units]) |
| `safe_write` | `write_atomic` (and document durability separately) |
| `get_or_default` | `port_or_default` with the missing states listed |

**Do not use when.**

- The name belongs to a published API, a wire protocol, a database
  column, or a generated binding; renaming breaks consumers, so report
  it instead.
- The project's glossary uses the term consistently; keep it.
- The problem is competing synonyms rather than a misleading name; use
  [one concept, one term][one-term].

**Example.** `parse_release_date` names the operation and the result,
and its docstring states the accepted format:

```python
def parse_release_date(text: str) -> date:
    """Accept only YYYY-MM-DD; '03/04/2025' is ambiguous and is rejected."""
```

The Rust `parse_duration` returns `std::time::Duration`, so the unit
travels with the value and the name needs no suffix.

**Cost removed.** Wrong calls made because the name promised a
different contract, such as treating `cancel()` as "stopped". A rename
is complete only when `rg -w old_name` finds 0 references outside
changelogs.

**Verify.**

1. Before renaming, find every reference: `rg -w name`, generated code,
   serialized fields, and configuration keys.
1. After renaming, the build, the tests, and `rg -w old_name` show no
   remaining use. Published names stay unchanged or are deprecated per
   [now is better than never](#now-is-better-than-never).

## Special cases aren't special enough to break the rules

**Definition.** A general algorithm that already handles edge inputs,
such as empty input or a remainder, gets no extra branches for them.

**Use when.** Code checks `len == 0`, `len == 1`, or "last element"
before logic that would produce the same result anyway.

**Do not use when.** The general rule gives a wrong or undefined result
for the edge case, such as the mean of an empty list or division by
zero. That edge case needs an explicit error; see
[refuse to guess](#refuse-the-temptation-to-guess).

**Example.** Python:

```python
def chunks(items: Sequence[T], size: int) -> list[list[T]]:
    """Empty input and a short last chunk follow the general rule."""
    if size < 1:
        raise ValueError("size must be at least 1")
    return [list(items[i : i + size]) for i in range(0, len(items), size)]
```

The replaced version had separate branches for empty input, input
shorter than one chunk, and the remainder.

**Cost removed.** Branches that must stay consistent with the general
path; the old version had 3. The test compares both versions for all
lengths 0 to 11 and sizes 1 to 5 (60 cases).

**Verify.**

1. Remove the special branch and run the edge-case tests. If they still
   pass, the branch was redundant.
1. The branch count drops (`rg -c 'if len' file`).

## Although practicality beats purity

**Definition.** A measured need may break a rule if the exception is
local, stated, and tested: local mutation behind a pure interface, a
platform branch, or a documented lint suppression.

**Use when.** A measurement or external constraint shows the "pure"
form fails a requirement, such as a time budget, a platform API, or a
compatibility promise.

**Do not use when.** The only argument is preference or an unmeasured
performance guess.

**Example.** Python:

```python
def build_index(words: Iterable[str]) -> dict[str, list[int]]:
    index: dict[str, list[int]] = {}
    for position, word in enumerate(words):
        index.setdefault(word, []).append(position)
    return index
```

The immutable variant in `test_examples.py` rebuilds the dict for every
word and returns the same result.

**Cost removed.** Time spent copying the dict. Measured with
`sh assets/examples/zen-of-python/verify.sh measure` (2,000 words, 500
distinct words, best of 7 runs of 10 calls): 0.0013 s against 0.025 to
0.028 s, 19 to 22 times faster. The function stays pure from the caller's
view.

**Verify.**

1. The exception carries its evidence: a benchmark command and the
   observed numbers, or the constraint it satisfies.
1. The caller-visible contract is tested: same output as the pure form,
   and no mutation of the input.

## Unless explicitly silenced

**Definition.** Code may ignore an error when it names the specific
error, limits the ignored region to the one operation that raises it,
and states why the error is expected. Every other failure follows
[specific error handling][errors].

**Use when.** The caller's desired outcome already holds: removing a
file that is gone, creating a directory that exists, or cancelling a
finished task.

**Do not use when.**

- The silenced type is broad (`Exception`, `OSError`, `io::Error` of
  any kind), which hides unrelated failures such as permission errors.
- The suppression covers several statements, so the expected error can
  come from the wrong line.

**Example.** Python:

```python
def remove_if_present(path: Path) -> None:
    """Silence exactly one expected error: the file is already gone."""
    with suppress(FileNotFoundError):
        os.remove(path)
```

Rust ([`explicit.rs`][explicit-rs]):

```rust
fn remove_if_exists(path: &Path) -> io::Result<()> {
    match fs::remove_file(path) {
        Err(error) if error.kind() == ErrorKind::NotFound => Ok(()),
        other => other,
    }
}
```

Both examples still report the error from removing a directory; the run
prints `directory error kept (PermissionDenied)` on macOS.

**Cost removed.** Retry and cleanup paths no longer fail on an expected
condition, and unexpected errors stay visible. ruff's `SIM105` rewrites
`try`/`except`/`pass` into `suppress(...)`, which makes the silencing
explicit but does not narrow it; the scanner's `wide-suppress` and
`silenced-except` kinds check the narrowing.

**Verify.**

1. `zen_scan.py` reports no `wide-suppress`, and each remaining
   `silenced-except` has a comment naming the expected condition.
1. A test triggers a different error in the same call, such as removing
   a directory, and asserts that it propagates.

## Refuse the temptation to guess

**Definition.** When input or configuration allows more than one
meaning, the code fails with an error naming the ambiguity instead of
picking one. The same holds for the author: a fact about API behavior,
units, ownership, concurrency, platform behavior, formats, or error
semantics is confirmed or marked unverified, never guessed into
plausible-looking code.

**Use when.**

- Formats with several readings: `03/04/2025`, numbers without units
  (`timeout = 30`), time zones.
- Two sources conflict, such as a renamed configuration key present
  under both names.
- The task depends on an unknown external contract, such as a limit, a
  version, a unit, or an API's consumers, that neither the repository,
  its dependencies' documentation, nor a run establishes. Ask or read
  the source; never invent it.

**Do not use when.** A documented default resolves the input to one
meaning, such as ISO 8601 dates or a unit fixed in the schema, or the
fact is verified and the change states where (doc link, test, command).

**Example.** Python:

```python
def read_port(settings: Mapping[str, str]) -> int:
    """Refuse to pick one when the old and new key disagree."""
    new, old = settings.get("port"), settings.get("listen_port")
    if new is not None and old is not None and new != old:
        raise ValueError(f"port={new!r} conflicts with listen_port={old!r}")
    chosen = new if new is not None else old
    if chosen is None:
        raise KeyError("port")
    return int(chosen)
```

Rust rejects a duration without a unit:

```text
$ ./explicit
guess: missing unit in "30"; use ms, s, or m
```

For an external fact, read the signature instead of assuming seconds.
Not:

```python
response = client.get(url, timeout=30)  # seconds
```

Instead, after reading the signature:

```python
import inspect

print(inspect.signature(client.get))  # confirms the parameter is timeout_ms
response = client.get(url, timeout_ms=30_000)
```

Or, when it cannot be confirmed:

```python
response = client.get(url, timeout=30)  # UNVERIFIED: unit of timeout
```

**Cost removed.** Configurations that load but mean something else,
such as `listen_port=81` silently ignored in favor of `port=80`, and
confidently wrong code that passes review because it looks finished. The
mutant `settings.get("port") or settings["listen_port"]` returns 80
without an error, and `test_guessing_mutant_is_rejected` detects it.

**Verify.**

1. Every ambiguous form under Use when has a test that expects an
   error; `parse_release_date` rejects `03/04/2025`, `2025-4-3`, and
   `20250403`.
1. The error message names both readings or both sources, so the user
   can resolve it.
1. The change description lists each external fact the code relies on
   and its source; `rg -n 'UNVERIFIED|TODO\(verify\)' <changed files>`
   lists open assumptions, and each appears in the report.

## There should be one obvious way to do it

**Definition.** Each operation has one supported entry point, and each
fact has one source of truth. PEP 20's follow-up line, "Although that
way may not be obvious at first unless you're Dutch", is read here as:
the canonical way may need documentation. Document it instead of adding
a second way. That includes the repository's existing way: a change does
not introduce a pattern, helper layer, client, or dependency the rest of
the repository does not use.

**Use when.**

- Two public functions do the same thing (`load_config` and
  `read_config`).
- Two constructors differ only in name.
- A value is parsed in two places with slightly different rules.
- Before adding a file, dependency, base class, or helper module.

**Do not use when.**

- The variants serve different needs, such as a streaming and a
  whole-document parser, or a sync and an async API. Those are two
  operations, not two ways.
- The task explicitly asks for a new pattern or a migration to one.

**Example.** Go ([`surface/config.go`][surface-go]) exports one
constructor and keeps the key normalization helper unexported:

```go
// Parse is the only exported way to create a Config.
func Parse(text string) (Config, error) {
    values := map[string]string{}
    for _, line := range strings.Split(text, "\n") {
        line = strings.TrimSpace(line)
        if line == "" {
            continue
        }
        key, value, ok := strings.Cut(line, "=")
        if !ok {
            return Config{}, errors.New("missing '=' in " + line)
        }
        values[normalize(key)] = strings.TrimSpace(value)
    }
    return Config{values: values}, nil
}
```

A repository that calls HTTP through `internal/httpclient` gets no
`requests.get(...)` in a new module because it is shorter:

```python
from internal import httpclient


def fetch_invoice(url: str) -> bytes:
    return httpclient.get(url).content
```

**Cost removed.** Behavior drift between duplicates, and the question
"which one do I use?" that every later reader and agent must reconcile.
Measured: `go doc -short` lists 1 exported function. In Python,
`test_public_surface_is_all` compares the names in `__all__` with
`dir(module)`.

**Verify.**

1. Count the operation's public entry points before and after:
   `go doc -short`, `__all__`, or exported symbols.
1. Published duplicates go through
   [deprecation](#now-is-better-than-never); internal duplicates are
   deleted along with their callers.
1. `git diff --name-status <base> | rg '^A'` lists new files, and
   `git diff <base> -- '*requirements*' '*package.json' '*go.mod'
   '*Cargo.toml' '*.csproj'` shows new dependencies; the change
   description gives a reason for each.

## Now is better than never

**Definition.** Announce a decision that changes callers when you make
it, in a machine-checkable form. For a removal, that is a deprecation
warning now, not a note to remove it "someday".

**Use when.** A public name, option, or behavior is being replaced, and
some callers cannot be updated in this change.

**Do not use when.** All callers are in the repository; update them and
delete the old name in the same change.

**Example.** Python ([`surface.py`][surface-py]):

```python
def read_config(text: str) -> dict[str, object]:
    """Deprecated alias of load_config; warns now, removed in 3.0."""
    warnings.warn(
        "read_config is deprecated; use load_config (removal in 3.0)",
        DeprecationWarning,
        stacklevel=2,
    )
    return load_config(text)
```

`stacklevel=2` attributes the warning to the caller's line; the test
asserts that the warning's filename is the test file.

**Cost removed.** Removals that surprise callers. Under
`python -W error::DeprecationWarning`, a call to `read_config` fails
while `load_config` passes; `verify.sh` runs both.

**Verify.**

1. The test suite runs with deprecation warnings as errors, and only
   the deprecated path fails.
1. The warning text names the replacement and the removal version.

## Although never is often better than right now

**Definition.** Add no public surface, option, or abstraction before a
caller needs it. Private code can change freely; published code becomes
a promise. The [file layout decision order][layout] applies the same rule
to each declaration's visibility.

**Use when.**

- A helper is written for one module.
- A configuration option is "nice to have".
- An unverified change would be irreversible, such as a data migration
  or a public API.

**Do not use when.** A caller outside the module needs the function
today; export it with tests of its contract.

**Example.** Python keeps `_with_defaults` private and lists the public
names in `__all__`:

```python
__all__ = ["build_index", "is_power_of_two", "load_config", "read_config"]


def _with_defaults(data: Mapping[str, object]) -> dict[str, object]:
    """Private until a caller outside this module needs it."""
    return {"retries": 3, **data}
```

Go reaches the same result with a lowercase `normalize`.

**Cost removed.** Unrequested compatibility obligations. The tests pin
the public symbol count: `__all__` equals the module's non-underscore
names.

**Verify.**

1. The diff adds no exported name without a caller outside its module.
1. Irreversible steps have a dry run or backup, and the report shows
   its output before the real run.

## If the implementation is hard to explain

**Definition.** PEP 20 pairs "If the implementation is hard to explain,
it's a bad idea" with "If the implementation is easy to explain, it may
be a good idea". This skill's test: the doc comment states in one or two
sentences why the code is correct, and each sentence maps to a test
assertion. If no such comment can be written, simplify the code. An
easy explanation is necessary, not sufficient ("may be").

**Use when.** Code relies on a trick (bit manipulation, clever indexing,
implicit ordering) or on an invariant the code does not show.

**Do not use when.** The code is plain; a comment restating it adds
nothing.

**Example.** Python:

```python
def is_power_of_two(n: int) -> bool:
    """A positive power of two has exactly one set bit, and n & (n - 1)
    clears the lowest set bit, so the result is zero only for such n."""
    return n > 0 and n & (n - 1) == 0
```

The explanation says "positive": the mutant without `n > 0` returns
`True` for 0, and the exhaustive test over -4..4096 against
`bin(n).count("1") == 1` rejects it.

**Cost removed.** Tricks with unwritten limits; 0 is this idiom's
classic bug. The test makes the explanation checkable.

**Verify.**

1. Each claim in the comment has a test, and mutants that break a claim
   fail it.
1. A trick kept for speed carries its benchmark, as in
   [practicality](#although-practicality-beats-purity).

## Namespaces are one honking great idea

**Definition.** Names reach code through a qualifier that shows where
they come from: `module.name`, `pkg.Func`, `ns::item`, `import * as ns`.
Star imports and glob `use` statements drop the qualifier.

**Use when.**

- A file uses `from x import *`, `use crate::a::*;` outside a prelude,
  or `import static ....*`.
- Two modules export the same name.

**Do not use when.** The language or library designs the glob for this
purpose, such as a Rust `prelude` module or `from __future__`. Test
modules keep `use super::*;`.

**Example.** Python: `from os import *` rebinds the builtin `open`:

```python
namespace = {}
exec("from os import *", namespace)
assert namespace["open"] is os.open  # not the builtin open()
```

TypeScript ([`namespaces/main.ts`][ns-ts]): two modules both export
`normalize`:

```ts
import * as text from "./text.ts";
import * as url from "./url.ts";

text.normalize(" X ");                  // "x"
url.normalize("HTTPS://Example.com");   // "https://example.com/"
```

**Cost removed.** Shadowed names. After `from os import *`,
`open("f.txt")` calls `os.open` and fails with a `TypeError` about the
missing `flags` argument. `zen_scan.py` counts `star-import` findings;
ruff's `F403` reports them too.

**Verify.**

1. `zen_scan.py` reports 0 `star-import`. For Rust, review each hit of
   `rg -n 'use .*::\*;' src` outside preludes and tests.
1. The tests pass with imports in qualified form.

[pep20]: https://peps.python.org/pep-0020/
[verify]: ../assets/examples/zen-of-python/verify.sh
[churn]: agent-failure-modes.md#unrequested-churn
[guard]: function-shape.md#guard-clauses
[sparse]: function-shape.md#lookup-table-instead-of-nested-conditional-expressions
[errors]: state-errors-comments.md#specific-error-handling-with-context
[ambient]: state-errors-comments.md#explicit-dependencies-instead-of-ambient-state
[extract]: function-shape.md#when-not-to-extract-a-function
[units]: names-and-types.md#units-in-names-or-types
[one-term]: names-and-types.md#one-concept-one-term
[layout]: file-layout.md#the-decision-order
[explicit-py]: ../assets/examples/zen-of-python/python/explicit_errors.py
[explicit-ts]: ../assets/examples/zen-of-python/langs/ts/explicit.ts
[explicit-rs]: ../assets/examples/zen-of-python/langs/rust/explicit.rs
[java-before]: ../assets/examples/zen-of-python/langs/java/SimpleBefore.java
[java-after]: ../assets/examples/zen-of-python/langs/java/SimpleAfter.java
[structure-py]: ../assets/examples/zen-of-python/python/structure.py
[before-py]: ../assets/examples/zen-of-python/python/structure_before.py
[retry-go]: ../assets/examples/zen-of-python/langs/go/retry/main.go
[surface-go]: ../assets/examples/zen-of-python/langs/go/surface/config.go
[surface-py]: ../assets/examples/zen-of-python/python/surface.py
[ns-ts]: ../assets/examples/zen-of-python/langs/ts/namespaces/main.ts
