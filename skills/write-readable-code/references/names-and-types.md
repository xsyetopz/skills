# Names and types

Cards that make a value's meaning clear from its name or type. Python
examples are in
[`names_types.py`](../assets/examples/readable/python/names_types.py);
Rust and TypeScript equivalents are in
[`types/`](../assets/examples/readable/types/ids.rs).

## Contents

- One concept, one term
- Units in names or types
- Distinct identifier types
- Illegal states unrepresentable
- Predicate names
- No dumping-ground modules
- Name length follows scope

## One concept, one term

**Definition.** Each domain concept has exactly one canonical word in
identifiers, messages, and docs; different concepts never share a word.
One name for two concepts, or several names for one, makes readers infer
the wrong identity.

**Use when.**

- Introducing any new identifier: reuse the word the surrounding code uses
  (`repository`, not a new `repo` or `store`).
- Reviewing a change that adds a synonym for an existing concept, or any
  rename.

**Do not use when.**

- The task explicitly renames a concept; then rename every occurrence in
  the same change.

**Example.** Count competing terms with the bundled script:

```sh
python3 scripts/term_report.py src/ \
  --group repository=repository,repo,store \
  --group customer=customer,client,account
```

Output lists each term's occurrences and files; exit 1 means a competing
term appears. Identifiers are split on camelCase and snake_case, so
`userRepo` counts as `repo`.

A codebase uses `account` for the billing entity and `user` for the login
identity. A new `get_account(user_id)` that returns a login record merges
the two. Not:

```python
def get_account(user_id: int) -> dict[str, str]:
    # Returns the login record, not the billing account.
    return LOGINS[user_id]
```

Instead, one name per concept:

```python
def get_user(user_id: int) -> dict[str, str]:
    return LOGINS[user_id]


def get_account(account_id: int) -> dict[str, str]:
    return BILLING_ACCOUNTS[account_id]
```

**Cost removed.** Readers and agents treating one concept as two, or two as
one, which leads to wrong joins and wrong assumptions downstream. Metric:
competing-term occurrences; your diff must not raise it.

**Verify.**

1. Run the report on the base revision and on your change; the competing
   counts must not rise.
1. `python3 scripts/test_term_report.py` covers the splitting rules.

## Units in names or types

**Definition.** Every quantity with a unit carries it in its name
(`timeout_ms`, `size_bytes`) or, better, in its type (`Milliseconds`,
`Duration`, `Bytes`).

**Use when.**

- A number represents time, size, money, angle, distance, or a rate.
- Two call sites disagree about the unit (the classic 1000× bug).

**Do not use when.**

- A standard type already encodes it (`timedelta`,
  `std::time::Duration`, `java.time.Duration`, `TimeSpan`): use it.

**Example.**

```python
Milliseconds = NewType("Milliseconds", int)


def candidate_deadline_ms(
    start_ms: Milliseconds, timeout_ms: Milliseconds
) -> Milliseconds:
    return Milliseconds(start_ms + timeout_ms)
```

```rust
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord)]
pub struct Millis(pub u64);

pub fn deadline(start: Millis, timeout: Millis) -> Millis {
    Millis(start.0 + timeout.0)
}
```

`typing.NewType` is erased at run time and checked only by a type checker
([typing.NewType](https://docs.python.org/3/library/typing.html#newtype)).

**Cost removed.** Looking up callers to learn the unit.

**Verify.**

1. `rg -n '\b(timeout|delay|interval|size|length)\b\s*[:=]' src/` lists
   unit-less names to review.
1. The type checker accepts the change (`pyright`, `tsc --noEmit`,
   `cargo check`).

## Distinct identifier types

**Definition.** Give different kinds of identifier different types, even
when they share a representation, so passing one for the other fails type
checking.

**Use when.**

- A function takes two or more IDs of the same primitive type
  (`user_id: int, tenant_id: int`).

**Do not use when.**

- The value crosses a serialization boundary and the wrapper would change
  the wire format: convert at the boundary instead.

**Example.** Python, TypeScript, and Rust:

```python
UserId = NewType("UserId", int)
TenantId = NewType("TenantId", int)


def candidate_membership_key(user_id: UserId, tenant_id: TenantId) -> str:
    return f"{tenant_id}:{user_id}"
```

```ts
declare const brand: unique symbol;
type Brand<T, Name extends string> = T & { readonly [brand]: Name };

export type UserId = Brand<number, "UserId">;
export type TenantId = Brand<number, "TenantId">;
```

```rust
pub struct UserId(pub u64);
pub struct TenantId(pub u64);

pub fn membership_key(user: UserId, tenant: TenantId) -> String {
    format!("{}:{}", tenant.0, user.0)
}
```

**Cost removed.** Silent argument swaps. Measured: the swapped call is
rejected by `rustc` (E0308), `tsc` (TS2345), and `pyright`
(`reportArgumentType`), while the `int`-typed baseline accepts it.

**Verify.**

1. `sh assets/examples/readable/verify.sh types` compiles the correct files and
   asserts each misuse file fails with the expected diagnostic.

## Illegal states unrepresentable

**Definition.** Model a value that is in exactly one of several states as
one enum (or tagged union), not several booleans, so impossible
combinations cannot be constructed.

**Use when.**

- Two or more booleans describe one lifecycle (`is_started`, `is_done`,
  `is_failed`).
- Code tests flag combinations in a fixed order to decide the state.

**Do not use when.**

- The flags are independent (`is_admin` and `is_verified`).

**Example.**

```python
class UploadState(enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class CandidateUpload:
    state: UploadState = UploadState.PENDING
```

**Cost removed.** Four booleans allow 16 states for 5 meaningful ones;
`baseline_describe` needs 5 branches (CCN 5) to pick a precedence, the enum
version needs none (CCN 1).

**Verify.**

1. The oracle maps each meaningful boolean combination to the enum and
   compares descriptions.
1. Make adding a state a compile error. In TypeScript, add a `default`
   that assigns the value to `never`. In Rust, and in Java switch
   expressions over a sealed type or enum, list every case and add no `_`
   arm or `default`: a catch-all silently accepts the new state.

## Predicate names

**Definition.** Boolean functions and variables read as yes/no questions:
`is_valid`, `has_header`, `can_retry`, `should_flush`.

**Use when.**

- Naming any boolean-returning function or boolean variable.

**Do not use when.**

- The language convention differs (Ruby `valid?`, Lisp `p` suffix): follow
  the language.

**Example.**

```python
def is_yaml_path(path: str) -> bool:
    return path.endswith((".yml", ".yaml"))
```

replaces `check(path)`, which says neither what it checks nor what `True`
means.

**Cost removed.** Opening the function to learn what `True` means.

**Verify.**

1. `rg -n 'def (check|validate|verify)_?\w*\(.*\) -> bool' src/` lists
   boolean functions with verb names to review.

## No dumping-ground modules

**Definition.** Modules are named after what they contain (`invoice_parse`,
`retry_policy`), never `utils`, `helpers`, `misc`, `common`, or `stuff`.

**Use when.**

- You are about to add to a `utils` module or create one.

**Do not use when.**

- The repository already has a `utils` convention you were not asked to
  change: add to the most specific existing module and report the issue.

**Example.** Move `format_money`, `retry_request`, and `slugify` out of
`utils.py` into `money.py`, `http_retry.py`, and `text.py`, next to their
callers' domain. Not, in `utils.py`:

```python
import re
import time


def format_money(cents: int) -> str:
    return f"{cents // 100}.{cents % 100:02d}"


def retry_request(send, attempts: int = 3):
    for attempt in range(attempts):
        try:
            return send()
        except ConnectionError:
            if attempt == attempts - 1:
                raise
            time.sleep(2**attempt)


def slugify(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
```

Instead, `money.py`:

```python
def format_money(cents: int) -> str:
    return f"{cents // 100}.{cents % 100:02d}"
```

`http_retry.py`:

```python
import time


def retry_request(send, attempts: int = 3):
    for attempt in range(attempts):
        try:
            return send()
        except ConnectionError:
            if attempt == attempts - 1:
                raise
            time.sleep(2**attempt)
```

`text.py`:

```python
import re


def slugify(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
```

**Cost removed.** Searching a grab-bag module to find or place code.

**Verify.**

1. `fd -t f '(utils|helpers|misc|common)\.' src/` must not list a new file
   in your diff.

## Name length follows scope

**Definition.** Short names (`i`, `x`, `n`) suit a scope of a few lines
and a conventional meaning; names that live longer or cross functions spell
out their meaning (`remaining_bytes`).

**Use when.**

- Naming loop indices, lambda parameters, and math variables with
  conventional meaning.

**Do not use when.**

- The name crosses a function boundary or lives longer than a screen:
  there `data`, `tmp2`, `val`, `thing`, `rem` make the reader trace the
  value.

**Example.**

```python
for i, line in enumerate(lines):  # i and line are clear in 3 lines
    ...

remaining_bytes = content_length - bytes_read  # used 40 lines later
```

**Cost removed.** Backtracking to a definition to learn meaning.

**Verify.**

1. List new identifiers of one to three characters with
   `git diff -U0 | rg '^\+.*\b[a-z]{1,3}\s*='` and confirm each has a
   small scope.
