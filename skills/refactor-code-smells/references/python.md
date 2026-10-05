# Python

Read when replacing a branch chain, flag argument, string state, or long parameter list in Python.
Check the repository's minimum Python first: `match` needs 3.10 and `assert_never` 3.11.

## Contents

- [Branch Chains](#branch-chains)
- [Lookup Tables](#lookup-tables)
- [Flag Arguments](#flag-arguments)
- [Guard Clauses](#guard-clauses)
- [Duplicated Branches](#duplicated-branches)
- [Primitive Obsession](#primitive-obsession)
- [Long Parameter Lists](#long-parameter-lists)
- [Dead Shims](#dead-shims)

## Branch Chains

`match` was added in Python 3.10 (PEP 634, [reference][r1]). The interpreter does not check
exhaustiveness; type checkers do. mypy checks `match` over `Literal` and `Enum` ([mypy][r2]).
`typing.assert_never` (3.11) asks the checker to confirm a line is unreachable ([docs][r3]).

```python
from enum import Enum
from typing import assert_never

class Mode(Enum):
    READ = "read"
    WRITE = "write"

def label(mode: Mode) -> str:
    match mode:
        case Mode.READ:
            return "r"
        case Mode.WRITE:
            return "w"
        case _ as unreachable:
            assert_never(unreachable)
```

Lint: Ruff `PLR1714` rewrites repeated `==` on one value to `in` ([rule][r4]).

## Lookup Tables

A dict `{"a": fa, "b": fb}[k]()` has no exhaustiveness check unless the keys are typed with
`Literal` or a `TypedDict`; prefer `match` when a checker must catch a new member.

## Flag Arguments

A keyword-only parameter (`*`, PEP 3102, [PEP](https://peps.python.org/pep-3102/)) makes the flag
readable at the call site, which makes it a smaller smell. Ruff `FBT001` flags a boolean positional
parameter ([rule][r5]). Split into two functions when the flag selects different behavior (Fowler's
[Remove Flag Argument](https://refactoring.com/catalog/removeFlagArgument.html)).

```python
def export(rows, *, strict: bool = False): ...

export(rows, strict=True)
```

## Guard Clauses

No dedicated syntax: early `return` or `continue`. Ruff `RET505` flags `else` after `return`
([rule](https://docs.astral.sh/ruff/rules/superfluous-else-return/)), `PLR1702` flags too many
nested blocks ([rule](https://docs.astral.sh/ruff/rules/too-many-nested-blocks/)), and `SIM102`
flags a collapsible `if` ([rule](https://docs.astral.sh/ruff/rules/collapsible-if/)). Fowler:
[Replace Nested Conditional with Guard Clauses][r6].

## Duplicated Branches

Ruff `SIM114` flags `if` arms with identical bodies
([rule](https://docs.astral.sh/ruff/rules/if-with-same-arms/)); merge the conditions (Fowler's
[Consolidate Conditional Expression][r7]). Hoist lines shared by all branches out of them.

## Primitive Obsession

- Closed string set: `enum.StrEnum` (3.11,
  [docs](https://docs.python.org/3/library/enum.html#enum.StrEnum)) or `typing.Literal`
  ([docs](https://docs.python.org/3/library/typing.html#typing.Literal)).
- Distinct id or unit type: `typing.NewType` makes a distinct type for the type checker; at runtime
  it returns its argument unchanged
  ([docs](https://docs.python.org/3/library/typing.html#typing.NewType)). It does not validate.
- Compound value: a frozen dataclass ([docs](https://docs.python.org/3/library/dataclasses.html)).
  Fowler: [Replace Primitive with Object][r8].

```python
from typing import NewType

UserId = NewType("UserId", int)
```

## Long Parameter Lists

Ruff `PLR0913` reports too many arguments; its limit is the `lint.pylint.max-args` option
([rule](https://docs.astral.sh/ruff/rules/too-many-arguments/)). Group related parameters in a
dataclass; `@dataclass(kw_only=True)` and `KW_ONLY` (3.10) force keyword construction ([docs][r9]).
Fowler: [Introduce Parameter Object][r10].

## Dead Shims

`@warnings.deprecated` (3.13, PEP 702, [docs][r11]) marks code for removal. Follow [compatibility
removal](compatibility-removal.md) before deleting.

[r1]: https://docs.python.org/3/reference/compound_stmts.html#the-match-statement
[r2]: https://mypy.readthedocs.io/en/stable/literal_types.html#exhaustiveness-checking
[r3]: https://docs.python.org/3/library/typing.html#typing.assert_never
[r4]: https://docs.astral.sh/ruff/rules/repeated-equality-comparison/
[r5]: https://docs.astral.sh/ruff/rules/boolean-type-hint-positional-argument/
[r6]: https://refactoring.com/catalog/replaceNestedConditionalWithGuardClauses.html
[r7]: https://refactoring.com/catalog/consolidateConditionalExpression.html
[r8]: https://refactoring.com/catalog/replacePrimitiveWithObject.html
[r9]: https://docs.python.org/3/library/dataclasses.html#dataclasses.dataclass
[r10]: https://refactoring.com/catalog/introduceParameterObject.html
[r11]: https://docs.python.org/3/library/warnings.html#warnings.deprecated
