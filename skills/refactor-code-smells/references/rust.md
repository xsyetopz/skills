# Rust

Read when replacing a branch chain, bool parameter, primitive, or long parameter list in Rust. Check
the crate's edition and `rust-version`: let-else needs 1.65 and let chains need 1.88 and edition
2024.

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

`match` arms "must cover all possibilities", so a new variant is a compile error ([book][r1]). A `_`
arm removes that check: Clippy `wildcard_enum_match_arm` (restriction group) flags it because new
variants "can be missed" ([lint][r2]). Name every variant on an enum you own.

```rust
enum Mode { Read, Write }

fn label(mode: Mode) -> &'static str {
    match mode {
        Mode::Read => "r",
        Mode::Write => "w",
    }
}
```

`#[non_exhaustive]` has no effect inside the defining crate; downstream crates must add `_`
([reference][r3]). Model state as an enum
([book](https://doc.rust-lang.org/book/ch06-01-defining-an-enum.html)), not a `String`.

## Lookup Tables

A `const` array indexed by `mode as usize` loses the `match` check: adding a variant gives an index
panic or a length mismatch, not a clear error. Prefer `match` for a closed enum.

## Flag Arguments

Use a two-variant enum instead of `bool`; API Guidelines C-CUSTOM-TYPE says arguments "convey
meaning through types, not bool or Option" (`Widget::new(Small, Round)`,
[guidelines](https://rust-lang.github.io/api-guidelines/type-safety.html)). Rust has no named
arguments. Clippy `fn_params_excessive_bools` (pedantic) says boolean parameters "obscure meaning at
the call site" ([lint][r4]). Fowler: [Remove Flag
Argument](https://refactoring.com/catalog/removeFlagArgument.html).

```rust
enum Size { Small, Large }
fn widget(size: Size) -> Widget { /* ... */ }
```

## Guard Clauses

`let PATTERN = EXPR else { diverge };` (1.65) pairs "a refutable pattern and a diverging else block"
([release](https://blog.rust-lang.org/2022/11/03/Rust-1.65.0/)). The `?` operator returns early on
`Err` or `None` ([book][r5]). Let chains (`if let Some(x) = a && x > 0 {}`) are edition 2024 only
([1.88](https://blog.rust-lang.org/2025/06/26/Rust-1.88.0/)).

```rust
let Some(item) = queue.pop() else { return };
```

Lint: Clippy `manual_let_else` (pedantic) and `collapsible_else_if` (pedantic). Fowler: [Replace
Nested Conditional with Guard Clauses][r6].

## Duplicated Branches

Clippy `match_same_arms` (pedantic) flags arms with the same body; merge them with `|` patterns.
Hoist shared lines out of the arms (Fowler's [Slide
Statements](https://refactoring.com/catalog/slideStatements.html)).

## Primitive Obsession

A newtype `struct Meters(u32);` gives a distinct type
([book](https://doc.rust-lang.org/book/ch20-03-advanced-types.html)). API Guidelines C-NEWTYPE:
"Newtypes provide static distinctions". Fowler: [Replace Primitive with Object][r7].

## Long Parameter Lists

Clippy `too_many_arguments` (complexity) fires above 7 parameters by default
(`too-many-arguments-threshold`). Take an options struct or a builder (API Guidelines C-BUILDER).
Fowler: [Introduce Parameter Object][r8].

## Dead Shims

`#[deprecated(since, note)]` ([reference][r9]) marks code for removal. Follow [compatibility
removal](compatibility-removal.md) before deleting.

[r1]: https://doc.rust-lang.org/book/ch06-02-match.html#matches-are-exhaustive
[r2]: https://rust-lang.github.io/rust-clippy/master/index.html#wildcard_enum_match_arm
[r3]: https://doc.rust-lang.org/reference/attributes/type_system.html#the-non_exhaustive-attribute
[r4]: https://rust-lang.github.io/rust-clippy/master/index.html#fn_params_excessive_bools
[r5]: https://doc.rust-lang.org/book/ch09-02-recoverable-errors-with-result.html
[r6]: https://refactoring.com/catalog/replaceNestedConditionalWithGuardClauses.html
[r7]: https://refactoring.com/catalog/replacePrimitiveWithObject.html
[r8]: https://refactoring.com/catalog/introduceParameterObject.html
[r9]: https://doc.rust-lang.org/reference/attributes/diagnostics.html#the-deprecated-attribute
