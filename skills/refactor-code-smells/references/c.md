# C

Read when replacing a branch chain, flag argument, primitive, or long parameter list in C. Check the
language standard the build uses: designated initializers need C99, `_Static_assert` C11, and
`[[deprecated]]` C23.

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

Use an `enum` and a `switch`. GCC `-Wswitch` (enabled by `-Wall`) warns when an enum-typed `switch`
lacks a case, but "the presence of a default label prevents this warning" ([GCC][r1]). For a closed
enum, omit `default` so the warning fires. If you keep a `default`, `-Wswitch-enum` warns "even if
there is a default label". Clang enables `-Wswitch` by default and also has `-Wswitch-enum` and
`-Wcovered-switch-default` ([Clang][r2]). Enums convert to `int`, so the compiler does not stop a
stray integer.

```c
enum mode { MODE_READ, MODE_WRITE };

const char *label(enum mode m) {
    switch (m) {
    case MODE_READ:  return "r";
    case MODE_WRITE: return "w";
    }
    return "?";
}
```

## Lookup Tables

A designated-initializer array (C99) is a data-only table, but "omitted fields are implicitly
initialized" and "the length of the array is the highest value specified", so a new enumerator can
leave a NULL hole or no slot ([GCC](https://gcc.gnu.org/onlinedocs/gcc/Designated-Inits.html)).
Guard the size with `_Static_assert` (C11,
[reference](https://en.cppreference.com/w/c/language/_Static_assert.html)); it does not detect a
hole. Function-pointer tables hide control flow, so prefer `switch` when arms differ in behavior.

```c
enum color { RED, GREEN, COUNT };
static const char *const names[] = { [RED] = "red", [GREEN] = "green" };
_Static_assert(sizeof names / sizeof *names == COUNT, "names");
```

## Flag Arguments

Two functions or an enum instead of an `int` flag. Fowler: [Remove Flag
Argument](https://refactoring.com/catalog/removeFlagArgument.html).

## Guard Clauses

No dedicated syntax: early `return`, or `goto cleanup` when the function releases resources. Fowler:
[Replace Nested Conditional with Guard Clauses][r3].

## Duplicated Branches

The research found no C compiler flag for identical branch bodies. Fowler: [Consolidate Conditional
Expression][r4].

## Primitive Obsession

"A typedef declaration does not introduce a distinct type, it only establishes a synonym"
([reference](https://en.cppreference.com/w/c/language/typedef.html)). Wrap the value in a struct.

```c
typedef struct { int v; } UserId;
```

## Long Parameter Lists

Pass an options struct with designated initializers (C99, [reference][r5]); unnamed fields default
to zero. Fowler: [Introduce Parameter Object][r6].

```c
struct opts { int strict; int retries; };
int run(const struct opts *o);

run(&(struct opts){ .strict = 1 });
```

## Dead Shims

`[[deprecated("msg")]]` (C23, [reference][r7]). Follow [compatibility
removal](compatibility-removal.md) before deleting.

[r1]: https://gcc.gnu.org/onlinedocs/gcc/Warning-Options.html#index-Wswitch
[r2]: https://clang.llvm.org/docs/DiagnosticsReference.html#wswitch
[r3]: https://refactoring.com/catalog/replaceNestedConditionalWithGuardClauses.html
[r4]: https://refactoring.com/catalog/consolidateConditionalExpression.html
[r5]: https://en.cppreference.com/w/c/language/struct_initialization.html
[r6]: https://refactoring.com/catalog/introduceParameterObject.html
[r7]: https://en.cppreference.com/w/c/language/attributes/deprecated.html
