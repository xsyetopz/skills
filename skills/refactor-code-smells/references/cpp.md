# C++

Read when replacing a branch chain, flag argument, primitive, or long parameter list in C++. Check
the language standard the build uses: `enum class` is C++11, `std::variant` C++17, designated
initializers C++20.

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

Core Guidelines ES.70: "Prefer a switch-statement to an if-statement when there is a choice", so the
compiler can say whether all enum values are covered; ES.78 forbids implicit fallthrough
([guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines)). Enum.3 prefers `enum
class` (C++11, [reference](https://en.cppreference.com/w/cpp/language/enum.html)). GCC and Clang
`-Wswitch` and `-Wswitch-enum` work as in [C](c.md#branch-chains): omit `default` on a closed enum.

For alternatives of different types use `std::variant` with `std::visit` (C++17): the visitor must
handle every alternative or the call does not compile
([reference](https://en.cppreference.com/w/cpp/utility/variant/visit.html)). The cppreference
example names the overload helper `overloads`.

```cpp
template <class... Ts> struct overloads : Ts... { using Ts::operator()...; };

std::visit(overloads{
    [](int i) { return std::to_string(i); },
    [](const std::string& s) { return s; },
}, value);
```

## Lookup Tables

A `constexpr std::array` indexed by an enum loses `-Wswitch`; prefer `switch`, or `variant` with
`visit`, when a new member must fail the build.

## Flag Arguments

C++ has no named arguments. Replace `bool` with an `enum class`, or split into two functions
(Fowler's [Remove Flag Argument](https://refactoring.com/catalog/removeFlagArgument.html)).

```cpp
enum class Strict : bool { No, Yes };
void parse(const Input& in, Strict strict);
```

## Guard Clauses

Early `return`. Fowler: [Replace Nested Conditional with Guard Clauses][r1].

## Duplicated Branches

The research found no compiler flag for identical branch bodies. Fowler: [Consolidate Conditional
Expression][r2].

## Primitive Obsession

"Type alias ... does not introduce a new type", so `using UserId = int;` is not a strong type
([reference](https://en.cppreference.com/w/cpp/language/type_alias.html)). Guideline I.4: "Make
interfaces precisely and strongly typed". Use a struct with an `explicit` constructor, or an `enum
class`.

```cpp
struct UserId {
    explicit UserId(int v) : v(v) {}
    int v;
};
```

## Long Parameter Lists

Guideline I.23: "Keep the number of function arguments low" ([guidelines][r3]); a cause is a
"missing an abstraction", so pass a compound value as one object. An aggregate with designated
initializers (C++20) reads like named arguments, but designators must follow declaration order
([reference][r4]).

```cpp
struct Options { bool strict = false; int retries = 3; };
void run(const Options& o);

run({ .strict = true, .retries = 5 });
```

## Dead Shims

`[[deprecated("msg")]]` (C++14, [reference][r5]). Follow [compatibility
removal](compatibility-removal.md) before deleting.

[r1]: https://refactoring.com/catalog/replaceNestedConditionalWithGuardClauses.html
[r2]: https://refactoring.com/catalog/consolidateConditionalExpression.html
[r3]: https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines
[r4]: https://en.cppreference.com/w/cpp/language/aggregate_initialization.html
[r5]: https://en.cppreference.com/w/cpp/language/attributes/deprecated.html
