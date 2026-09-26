# Function shape

Cards that reshape a function's control flow without changing its
behavior. Every Python example is a runnable pair in
[`shape.py`](../assets/examples/readable/python/shape.py);
`test_examples.py` proves equivalence (including error type and message)
and `sh assets/examples/readable/verify.sh examples` asserts the metric
drop with [`python_function_metrics.py`](../scripts/python_function_metrics.py).
The C and TypeScript examples run under
[`zen-of-python/verify.sh`](../assets/examples/zen-of-python/verify.sh).

## Contents

- Function metrics and limits
- Guard clauses
- Phases: validate, prepare, execute
- Lookup table instead of nested conditional expressions
- Parameter object
- Dispatch table instead of an if/elif chain
- Explaining variables
- Split boolean flag arguments
- When not to extract a function

## Function metrics and limits

**Definition.** Mechanical measures of what a reader must hold in mind:

| Metric | Meaning | Target | Review above |
| --- | --- | --- | --- |
| NLOC | non-blank, non-comment lines of the function | ≤ 30 | 40 |
| Cyclomatic complexity (CCN) | 1 + number of decision points | ≤ 8 | 10 |
| Cognitive complexity | Sonar metric; nesting adds to the cost of each branch | ≤ 10 | 15 |
| Nesting depth | deepest block inside the body | ≤ 2 | 3 |
| Parameters | declared parameters (excluding `self`) | ≤ 4 | 6 |
| Local variables | distinct locals | ≤ 7 | 10 |

The targets are this skill's default policy (from the readability guide it
packages), not universal limits. Cyclomatic complexity is McCabe's measure
([McCabe 1976](https://doi.org/10.1109/TSE.1976.233837)); NIST SP 500-235
recommends 10 as a default upper limit
([NIST SP 500-235][nist-sp-500-235]).
Cognitive complexity is defined in SonarSource's white paper
([Cognitive Complexity][cognitive-complexity]).

**Use when.**

- Reviewing a diff: measure the touched functions before and after.
- Choosing which function to restructure first: start with the highest
  nesting or CCN in the code you must change.

**Do not use when.**

- The only goal is getting a straight-line function under the NLOC
  target: a 45-line sequence of steps can read better than five 9-line
  fragments that force jumps.
- Comparing metrics across languages or tools: each tool counts
  differently.

**Example.** Default to the repository's linter; without one, use lizard
(20+ languages) or, for Python, the bundled script:

```sh
# Any language lizard supports; exits 1 when a threshold is exceeded.
uvx lizard -C 8 -L 40 -a 4 -ENS -T max_nested_structures=2 -w src/

# Python: lizard 1.24.0's nesting column (NS) accumulates across a Python
# file, so use the bundled AST-based script for Python nesting.
python3 scripts/python_function_metrics.py src/ \
  --max-nesting 2 --max-ccn 8 --max-params 4 --max-nloc 40

# Repository linters that already enforce these rules:
ruff check --select C901,PLR0913,PLR0912,PLR0915 src/     # Python
bunx eslint --rule '{"complexity":["error",8],"max-depth":["error",2]}' .
cargo clippy -- -W clippy::too_many_arguments -W clippy::cognitive_complexity
```

Rule references: [ruff C901][ruff-c901],
[ruff PLR0913](https://docs.astral.sh/ruff/rules/too-many-arguments/),
[ESLint complexity](https://eslint.org/docs/latest/rules/complexity),
[ESLint max-depth](https://eslint.org/docs/latest/rules/max-depth),
[Clippy lints](https://rust-lang.github.io/rust-clippy/master/index.html),
[lizard](https://github.com/terryyin/lizard).

**Cost removed.** Unmeasured complexity growth. The metrics stand in for
the cost: a reader tracks every open branch and nesting level.

**Verify.**

1. Record the metrics of every function you touch before editing.
1. After editing, the same command shows each touched function at or
   below its previous value, and at or below the targets unless a card
   below explains why not.

## Guard clauses

**Definition.** Handle each precondition failure first with an early
`return`/`raise`/`continue`, so the normal path runs at the lowest
indentation, top to bottom. This is the skill's reading of PEP 20's "Flat
is better than nested".

**Use when.**

- The happy path sits inside several nested `if`s whose `else` branches
  only reject input.

**Do not use when.**

- Guards would change the order of the checks: keep the original order,
  because error messages and side effects depend on it.
- The function must release a resource on every exit and the language has
  no `with`/`using`/`defer`/RAII: each extra return risks a leak.
- The nesting mirrors real structure, such as nested data or a resource
  scope (`with`, `using`, `defer` blocks).
- A coding standard requires a single exit, such as MISRA C.

**Example.** Python:

```python
def candidate_ship_order(order: Mapping[str, object]) -> str:
    if not order.get("paid"):
        raise OrderError("order is not paid")
    if not order.get("items"):
        raise OrderError("order has no items")
    if not order.get("address"):
        raise OrderError("order has no address")
    if order.get("cancelled"):
        raise OrderError("order is cancelled")

    return "shipped"
```

C ([`flat.c`](../assets/examples/zen-of-python/langs/c/flat.c)):

```c
static enum status decide(const struct order *o) {
    if (!o->paid) {
        return HOLD_UNPAID;
    }
    if (o->items <= 0) {
        return HOLD_EMPTY;
    }
    if (o->address == NULL) {
        return HOLD_NO_ADDRESS;
    }
    return SHIP;
}
```

**Cost removed.** Nesting depth 4 → 1 in Python (measured by
`python_function_metrics.py`) and 3 → 1 in C (`zen-of-python/verify.sh`
measures the brace depth from the source). CCN stays 5 → 5: guard clauses
remove nesting, not decisions, and cognitive complexity penalizes nesting
where CCN ignores it.

**Verify.**

1. `python3 assets/examples/readable/python/test_examples.py` compares
   outcome tuples (result or exception type and message) for six orders,
   one per branch plus an empty order. The C program compares the flat and
   nested versions on all 12 input combinations.
1. `sh assets/examples/readable/verify.sh examples` prints
   `PASS guard-clauses: nesting 4 -> 1`;
   `sh assets/examples/zen-of-python/verify.sh` prints
   `brace depth inside function: nested 3, flat 1`.
1. Outside Python, measure with the project's linter, such as `gocognit`
   or clang-tidy's `readability-function-cognitive-complexity`.

## Phases: validate, prepare, execute

**Definition.** Lay a function out as separate phases (validate input,
prepare data, execute, handle the result). Extract a phase into a named
function when it has its own invariant, such as "parsing produces a valid
`InvoiceLine`".

**Use when.**

- Validation, conversion, and computation are interleaved inside one loop.
- A block changes abstraction level (from field checks to arithmetic).
- A long procedural function, typical of generated code, mixes several
  purposes: a 90-line `handle_request` that parses, validates, queries,
  formats, and logs becomes `parse`, `validate`, `load`, and `render`
  called in sequence.

**Do not use when.**

- The phases share so much state that the extracted function would take
  most of the caller's locals as parameters: that moves complexity into the
  signature.
- The function is a straight sequence of steps at one level of detail;
  length alone does not justify a split.

**Example.**

```python
@dataclass(frozen=True)
class InvoiceLine:
    price_cents: int
    quantity: int


def parse_invoice_line(raw: dict[str, object]) -> InvoiceLine:
    if "price_cents" not in raw or "quantity" not in raw:
        raise ValueError("line is missing price_cents or quantity")
    price = raw["price_cents"]
    quantity = raw["quantity"]
    if not isinstance(price, int) or not isinstance(quantity, int):
        raise ValueError("price and quantity must be integers")
    if price < 0 or quantity <= 0:
        raise ValueError("negative price or non-positive quantity")
    return InvoiceLine(price_cents=price, quantity=quantity)


def candidate_invoice_total(
    lines: list[dict[str, object]], tax_rate: float
) -> int:
    parsed = [parse_invoice_line(raw) for raw in lines]

    subtotal_cents = sum(line.price_cents * line.quantity for line in parsed)

    return round(subtotal_cents * (1 + tax_rate))
```

The `handle_request` split, abridged; each helper holds one former phase:

```python
def handle_request(raw: bytes) -> str:
    request = parse(raw)
    validate(request)
    rows = load(request)
    LOG.info("served %d orders", len(rows))
    return render(rows)
```

**Cost removed.** The baseline function: nesting 4, CCN 8, 16 NLOC. After:
`candidate_invoice_total` nesting 0, CCN 3; `parse_invoice_line` nesting 1,
CCN 7. Total decisions barely change; each function now has one job and
one level of detail.

**Verify.**

1. The oracle compares totals and exceptions for empty input, valid lines,
   a negative price, a float price, and a missing key.
1. Behavior change to watch: the candidate validates **all** lines before
   summing; the baseline raised on the first bad line mid-sum. Both raise
   the same exception for the first bad line, so the result here is the
   same. Recheck this for any function with side effects inside the loop.

## Lookup table instead of nested conditional expressions

**Definition.** Replace chained conditional expressions (`a if x else b if
y else c`) with an ordered table of (limit, result) pairs or an explicit
`if`/`elif` block, one decision per line, so each case can be read, tested,
and changed on its own. This is the skill's reading of PEP 20's "Sparse is
better than dense".

**Use when.**

- A conditional expression contains another conditional expression, in
  any language (`?:` chains in C-family languages and TypeScript).
- The thresholds are data (bands, tiers, ranges).
- One expression holds several conditions: a nested comprehension with
  filters, or a long boolean expression (see also
  [explaining variables](#explaining-variables)).

**Do not use when.**

- There is one condition: `a if x else b` is clear.
- The dense form is a standard idiom of the language, such as a one-line
  list comprehension or `x if x is not None else y`.

**Example.** Python, where the thresholds are data:

```python
_SHIPPING_BANDS = ((100, "letter"), (2000, "small"), (10000, "medium"))


def candidate_shipping_band(weight_grams: int) -> str:
    for upper_limit_grams, band in _SHIPPING_BANDS:
        if weight_grams <= upper_limit_grams:
            return band
    return "freight"
```

TypeScript ([`sparse.ts`](../assets/examples/zen-of-python/langs/ts/sparse.ts)),
where the branches are behavior. The dense form:

```ts
return count === 0 ? "" : level === "error"
  ? `E${count > 99 ? "99+" : count}` : level === "warn"
  ? `W${count > 99 ? "99+" : count}` : `${count}`;
```

The sparse form:

```ts
if (count === 0) {
  return "";
}
if (level === "info") {
  return String(count); // uncapped: the dense form hid this exception
}
const shown = count > 99 ? "99+" : String(count);
const prefix = level === "error" ? "E" : "W";
return prefix + shown;
```

The first sparse rewrite capped every level at `99+`, and the equivalence
test failed with `'99+' !== '100'`: the dense form silently left `info`
counts uncapped. The sparse form keeps that behavior on its own line,
where a reviewer can decide whether it is intended.

**Cost removed.** Reading nested expressions right to left, and hidden
cases that surface only when the expression is split. Python: CCN 4 → 3.
Nesting rises (0 → 2) because the metric counts the loop and `if` but not
expressions; judge this card by how the data reads, not by nesting.

**Verify.**

1. The Python oracle checks every boundary: 0, 100, 101, 2000, 2001,
   10000, 10001. The TypeScript equivalence test covers 15 inputs.
1. An equivalence test over all branch combinations passes before the
   dense form is deleted.
1. Each exception the split exposes is reported as a question, not
   silently fixed.

## Parameter object

**Definition.** Group parameters that always travel together into one
immutable value type (`@dataclass(frozen=True)`, `record`, `struct`) and
pass that.

**Use when.**

- A function takes more than four parameters, several of the same type,
  and callers pass them positionally (easy to swap).
- The same group of parameters appears in several signatures.

**Do not use when.**

- The parameters are unrelated; bundling them hides the real dependencies.
- The object would be mutable and shared, which brings back action at a
  distance.

**Example.**

```python
@dataclass(frozen=True)
class ConnectionSettings:
    host: str
    port: int
    user: str
    database: str
    use_tls: bool
    timeout_ms: int
    application_name: str


def candidate_connect_url(settings: ConnectionSettings) -> str:
    scheme = "postgresqls" if settings.use_tls else "postgresql"
    return (
        f"{scheme}://{settings.user}@{settings.host}:{settings.port}/"
        f"{settings.database}?connect_timeout_ms={settings.timeout_ms}"
        f"&application_name={settings.application_name}"
    )
```

**Cost removed.** Parameters 7 → 1, and call sites name every field
(`ConnectionSettings(host=..., port=...)`), so swapping `user` and
`database` becomes visible.

**Verify.**

1. The oracle builds the same URL both ways.
1. `readable/verify.sh examples` prints `PASS parameter-object: params 7 -> 1`.
1. `rg -n 'baseline_connect_url\('` in a real change lists every caller;
   each must be migrated in the same change.

## Dispatch table instead of an if/elif chain

**Definition.** Map keys to functions in a dictionary (or `match`/`switch`
with one line per case) instead of a chain of equality tests.

**Use when.**

- An `if`/`elif` chain compares one value against constants and each
  branch does one thing.

**Do not use when.**

- Branches test different conditions or ranges.
- The language's `switch`/`match` checks exhaustiveness (Rust `match`,
  TypeScript discriminated unions, Java/C# switch on enums): use it, since
  the compiler then reports missing cases.

**Example.**

```python
_OPERATIONS = {
    "add": lambda left, right: left + right,
    "sub": lambda left, right: left - right,
    "mul": lambda left, right: left * right,
    "min": min,
    "max": max,
}


def candidate_apply(op: str, left: int, right: int) -> int:
    operation = _OPERATIONS[op]  # KeyError for unknown op, as before
    return operation(left, right)
```

**Cost removed.** CCN 6 → 1; adding an operation touches one line.

**Verify.**

1. The oracle compares all five operations and an unknown one (`KeyError`
   with the same message in both).
1. `readable/verify.sh examples`: `PASS dispatch-table: ccn 6 -> 1`.

## Explaining variables

**Definition.** Name each sub-condition of a compound boolean or each step
of a dense expression with a local variable whose name states its meaning.

**Use when.**

- A boolean expression mixes three or more concepts, or a reviewer asked
  what a sub-expression means.

**Do not use when.**

- The expression is already one concept (`count > 0`).

**Example.**

```python
def candidate_can_retry(status: int, attempt: int, elapsed_ms: int) -> bool:
    is_retryable_status = status == 429 or 500 <= status < 600
    has_attempts_left = attempt < 5
    is_within_deadline = elapsed_ms < 30_000
    return is_retryable_status and has_attempts_left and is_within_deadline
```

**Cost removed.** Decoding the expression in the reader's head. Metrics do
not move (CCN 4 → 4), so judge this card in review.

**Verify.**

1. The oracle compares all 45 combinations of status, attempt, and elapsed
   time, including each boundary.

## Split boolean flag arguments

**Definition.** Replace a `bool` parameter that selects between two
behaviors with two functions whose names state the behavior.

**Use when.**

- Call sites read `format_amount(x, True)` and a reader cannot tell what
  `True` means.

**Do not use when.**

- The boolean is data, not a behavior switch (`set_enabled(value)`).
- The two behaviors share most of their body; use an enum parameter
  instead (`Style.COMPACT`).

**Example.**

```python
def format_amount(cents: int) -> str:
    return f"{cents / 100:,.2f}"


def format_amount_compact(cents: int) -> str:
    return f"{cents / 100:.0f}"
```

**Cost removed.** CCN 2 → 1 per function, and call sites describe
themselves.

**Verify.**

1. The oracle compares both modes for 0, 5, 123456, and -250 cents.
1. `rg -n 'format_amount\([^)]*,\s*(True|False)\)'` finds no remaining
   flag calls after the migration.

## When not to extract a function

**Definition.** Extract a function for a stable concept (a name that
explains more than the code), not for syntactic similarity or line count.

**Use when.**

- Deciding whether to inline a helper that an earlier change extracted.

**Do not use when.**

- No exception applies. Never extract a helper that only renames one
  statement (`increment_index()` for `index += 1`), or a block that needs
  most of the caller's locals as parameters.

**Example.** Inline this:

```python
def _increment(value: int) -> int:
    return value + 1

count = _increment(count)
```

as `count += 1`. Keep `parse_invoice_line` (above): it has an invariant
and an informative name.

**Cost removed.** A jump to another location for no information.

**Verify.**

1. For each new helper in the diff, count call sites:
   `rg -c '\bhelper_name\('`. One call site and a one- or two-line body
   make it a candidate for inlining, unless the name documents a domain
   rule.

[nist-sp-500-235]: https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication500-235.pdf
[cognitive-complexity]: https://www.sonarsource.com/docs/CognitiveComplexity.pdf
[ruff-c901]: https://docs.astral.sh/ruff/rules/complex-structure/
