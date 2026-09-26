# Object, parameter, and ownership constructs

Cards that remove copies, moves, allocations, and atomic reference-count
operations at object boundaries. Pairs live in
[`constructs/objects.cpp`](../assets/examples/constructs/objects.cpp).
`verify.sh verify` checks equal results, then asserts the counted
benefit with the copy/move counting type or the counting
`operator new`; `verify.sh asm` asserts the atomic instructions.

Measured numbers are machine-specific: Apple M1 Max, macOS 27.0 arm64,
Apple clang 21.0.0, libc++ 21.1, `-std=c++23 -O2`. `COPIES`, `MOVES`,
and `ALLOC` lines come from `verify.sh verify`; times are medians from
`verify.sh time` on a shared, noisy machine; rerun a pair alone before
quoting it.

## Contents

- Guaranteed copy elision of prvalues
- Return a local by name (NRVO)
- Implicit move on return
- Non-const locals for values that will be moved
- std::move at the last use
- noexcept move constructor for vector growth
- Pass by value and move for sink parameters
- const reference for read-only parameters
- emplace_back instead of push_back of a temporary
- make_shared instead of shared_ptr from new
- unique_ptr instead of shared_ptr
- Pass shared_ptr by const reference

## Guaranteed copy elision of prvalues

**Definition.** Since C++17 ([P0135R1][p0135]), a prvalue of the same
class type initializes the destination object directly
([dcl.init.general]). No temporary is materialized, no copy or move
constructor runs, and the type need not be copyable or movable.
`T x = std::move(make());` defeats this: `std::move` turns the prvalue
into an xvalue, a temporary is materialized, and `x` is move-constructed
from it.

**Use when.**

- A factory returns by value (`return T{...};`) and the caller
  initializes a variable from the call.
- Code wraps a returned prvalue in `std::move`, or returns a non-movable
  type through an out-parameter only to avoid a copy.

**Do not use when.**

- The value is a named object: that is NRVO, which is not guaranteed
  (next card).
- Pre-C++17 targets must build the code: they still require an
  accessible copy or move constructor.

**Example.**

```cpp
Item make_item(int v) { return Item{v}; }

int elide_baseline(int v) {
  Item a = std::move(make_item(v)); // temporary + 1 move
  return a.value;
}
int elide_candidate(int v) {
  Item a = make_item(v); // constructed in place: 0 moves
  return a.value;
}
```

Runnable: `assets/examples/constructs/objects.cpp`.

**Cost removed.** One move construction and destruction per call. Measured:
`MOVES copy-elision: 1 -> 0`. Clang flags the baseline with
`-Wpessimizing-move` ("moving a temporary object prevents copy
elision").

**Verify.**

1. `verify.sh verify` checks the value and prints the `MOVES` line.
1. `verify.sh diagnose` asserts the warning on the baseline.

## Return a local by name (NRVO)

**Definition.** When a function returns a named non-volatile automatic
object of the return type, the copy/move "can be omitted by
constructing [it] directly into the function call's result object"
([class.copy.elision]/1.1). This is a permission, not a guarantee.
`return std::move(local);` turns the operand into an xvalue, which
disables the elision and forces a move.

**Use when.**

- A function builds a local and returns it: `T r; ...; return r;`.
- A diff adds `std::move` to a `return` of a local.

**Do not use when.**

- The function returns different locals from two `return` statements:
  elision is then unlikely, and the implicit move on return applies
  instead (next card). Do not add `std::move`.
- The function returns `return cond ? a : b;`: a conditional expression
  is not an id-expression, so neither elision nor the implicit move
  applies and the result is copied. Write two `return` statements
  instead.
- The returned name is a function parameter: parameters are never
  elided; they are implicitly moved.

**Example.**

```cpp
Item nrvo_baseline(int v) {
  Item r{v};
  r.value += 1;
  return std::move(r); // -Wpessimizing-move: 1 move
}
Item nrvo_candidate(int v) {
  Item r{v};
  r.value += 1;
  return r; // NRVO here: 0 moves
}
```

Runnable: `assets/examples/constructs/objects.cpp`.

**Cost removed.** One move per return. Measured: `MOVES nrvo: 1 -> 0`.
For a type with an expensive or absent move (a large `std::array`
member), the difference is a copy versus nothing.

**Verify.**

1. `verify.sh verify` checks the returned value and the `MOVES` line.
1. `verify.sh diagnose` asserts "moving a local object in a return
   statement prevents copy elision".

## Implicit move on return

**Definition.** An id-expression in a `return` that names an implicitly
movable entity (an automatic non-volatile object, or since C++23 also an
rvalue reference to one) is move-eligible and is treated as an rvalue
([expr.prim.id.unqual]/15; [P1825R0][p1825] for C++20,
[P2266R3][p2266] for C++23). `return param;` therefore moves; an
explicit `std::move` adds nothing.

**Use when.**

- A function returns a by-value parameter, or (C++23) a `T&&`
  parameter, by name.
- Code has `return std::move(x);` where `x` is such an entity: drop the
  cast.

**Do not use when.**

- The returned expression is a member (`return m_buf;`) or a
  subobject: it is not move-eligible. Moving from it needs an explicit
  `std::move` and leaves the member moved-from.
- The code must build as C++20 and returns a `T&&` parameter: before
  P2266 that returns a copy.

**Example.**

```cpp
Item ret_param_baseline(Item t) {
  t.value += 1;
  return std::move(t); // -Wredundant-move
}
Item ret_param_candidate(Item t) {
  t.value += 1;
  return t; // moved, never copied
}
Item ret_rref_candidate(Item &&t) { return t; } // C++23: moved
```

Runnable: `assets/examples/constructs/objects.cpp`.

**Cost removed.** None at run time; measured no difference:
`MOVES implicit-move-param: 1 -> 1 (no difference expected)` and
`COPIES implicit-move-rref (C++23): 0 (moves 1)`. The gain is less
review noise and no `-Wredundant-move` warnings.

**Verify.**

1. `verify.sh verify` asserts equal move counts and zero copies.
1. `verify.sh diagnose` asserts "redundant move in return statement".

## Non-const locals for values that will be moved

**Definition.** `std::move` on a `const T` yields `const T&&`, which
cannot bind to `T(T&&)` and selects the copy constructor. The code
compiles and silently copies.

**Use when.**

- A local is declared `const` and later passed through `std::move` into
  a container, member, or return.

**Do not use when.**

- The object is never moved: `const` then documents intent at no cost.

**Example.**

```cpp
void const_local_baseline(std::vector<Item> &out, int v) {
  Item const t{v};
  out.push_back(std::move(t)); // copy constructor
}
void const_local_candidate(std::vector<Item> &out, int v) {
  Item t{v};
  out.push_back(std::move(t)); // move constructor
}
```

Runnable: `assets/examples/constructs/objects.cpp`.

**Cost removed.** One copy per call. Measured:
`COPIES const-local: 1 -> 0`. For `std::string` or `std::vector`
values the copy is an allocation plus a memcpy.

**Verify.**

1. `verify.sh verify` checks both vectors hold equal values.
1. Run `rg -n 'const [A-Za-z_:<>]+ [a-z_]+ ?[{=]' src/` and check
   whether each such name later appears in `std::move(`.

## std::move at the last use

**Definition.** `std::move(x)` casts to an rvalue reference, so a move
constructor or move assignment is chosen; for standard containers and
strings that steals the heap buffer instead of copying it.

**Use when.**

- A named local or by-value parameter is passed to a sink
  (`push_back`, a setter, a constructor) and not used afterwards.

**Do not use when.**

- The object is read after the move: a moved-from standard library
  object is "valid but unspecified", so reading its value is a logic
  bug.
- The type has no move constructor or its move equals a copy
  (`std::array<int, N>`, trivially copyable structs): no gain.

**Example.**

```cpp
for (int i = 0; i < n; ++i) {
  std::string line = kLong; // 64 chars: heap allocated
  line += std::to_string(i);
  out.push_back(std::move(line)); // baseline: out.push_back(line)
}
```

Runnable: `assets/examples/constructs/objects.cpp`.

**Cost removed.** One heap allocation and copy per element. Measured:
`ALLOC move-last-use: 513 -> 257` (256 lines); time 15.75 -> 9.60 µs.

**Verify.**

1. `verify.sh verify` compares the two vectors, then the `ALLOC` line.
1. `clang-tidy -checks=performance-unnecessary-copy-initialization`
   flags other copies ([clang-tidy check][tidy-copy]). Not executed:
   clang-tidy is not installed on this machine.

## noexcept move constructor for vector growth

**Definition.** When `std::vector` reallocates, it moves elements only
if the move constructor is `noexcept` (or the type is not copyable);
otherwise it copies, to keep the strong guarantee ("If an exception is
thrown while inserting a single element at the end and T is
Cpp17CopyInsertable or `is_nothrow_move_constructible_v<T>` is true,
there are no effects", [vector.modifiers]). A defaulted move
constructor is `noexcept` when every member's move is.

**Use when.**

- A user-declared move constructor or move assignment lacks `noexcept`,
  and the type lives in a growing `std::vector` (or `std::deque`
  reallocation, `std::optional` wrapping).
- `static_assert(std::is_nothrow_move_constructible_v<T>)` fails.

**Do not use when.**

- The move can throw (it allocates): `noexcept` turns that throw into
  `std::terminate`. Fix the move instead, or accept copies.

**Example.**

```cpp
struct Row {
  std::string name;
  Row(Row &&o) noexcept : name(std::move(o.name)) {}
  // or: Row(Row &&) noexcept = default;
};
static_assert(std::is_nothrow_move_constructible_v<Row>);
```

Runnable: `assets/examples/constructs/objects.cpp` (`grow<Tracked<B>>`).

**Cost removed.** Every relocation copy. Measured:
`COPIES noexcept-move: 1023 -> 0` for 1000 `emplace_back` calls without
`reserve` (the candidate does 1023 moves instead). Time: 731 -> 715 ns,
no clear difference, because `Tracked` holds one `int` whose copy and
move cost the same. The gain scales with the real type's copy cost.

**Verify.**

1. `verify.sh verify` compares sizes and last values, then `COPIES`.
1. Add `static_assert(std::is_nothrow_move_constructible_v<T>)` next to
   the type so the property cannot regress.

## Pass by value and move for sink parameters

**Definition.** A function that stores its argument takes it by value
and moves it into place. Rvalue arguments are moved twice (cheap) and
never copied; lvalue arguments are copied once.

**Use when.**

- A constructor or setter stores a `std::string`, `std::vector`, or
  other movable owner, and callers often pass temporaries or
  `std::move`d values.

**Do not use when.**

- Callers pass lvalues into an object whose member already has enough
  capacity: `name = s;` (const&) reuses the member's buffer, while by
  value always builds a new string first. Measured:
  `ALLOC sink-param-lvalue-reuse: 1 -> 0` (by-value 1, const& 0).
- The function does not always store the argument: the by-value copy is
  wasted on the paths that do not.
- The type is expensive to move (`std::array` of many elements).

**Example.**

```cpp
struct WidgetVal {
  std::string name;
  void set(std::string s) { name = std::move(s); }
};
// baseline: void set(std::string const &s) { name = s; }
```

Runnable: `assets/examples/constructs/objects.cpp`.

**Cost removed.** The copy of an rvalue argument. Measured:
`ALLOC sink-param-rvalue: 2 -> 1` (the 1 left is the caller's
temporary).

**Verify.**

1. `verify.sh verify` checks both widgets hold equal names and prints
   both `ALLOC sink-param-*` lines.
1. Before choosing, count call sites passing lvalues versus rvalues
   (`rg -n '\.set\(' src/`).

## const reference for read-only parameters

**Definition.** A `T const&` parameter binds to the caller's object; a
by-value parameter of a non-trivial type copy-constructs it (for a
container, the buffer plus one allocation per element).

**Use when.**

- The function takes a `std::vector`, `std::string`, `std::map`, or
  another owning type by value and only reads it.

**Do not use when.**

- The type is small and trivially copyable (`int`, `double`,
  `std::string_view`, `std::span`, a two-pointer struct): pass by value.
  A reference adds an indirection and aliasing questions.
- The function stores or modifies a private copy: use the sink card.

**Example.**

```cpp
std::size_t total_len_candidate(std::vector<std::string> const &v) {
  std::size_t n = 0;
  for (auto const &s : v) n += s.size();
  return n;
}
// baseline: std::size_t total_len_baseline(std::vector<std::string> v)
```

Runnable: `assets/examples/constructs/objects.cpp`.

**Cost removed.** The deep copy. Measured:
`ALLOC const-ref-param: 65 -> 0` (64 strings of 64 chars); time
1594 -> 42 ns.

**Verify.**

1. `verify.sh verify` checks equal totals and the `ALLOC` line.
1. `rg -n '\((const )?std::(vector|string|map)<[^&]*> [a-z]' src/`
   finds remaining by-value container parameters.

## emplace_back instead of push_back of a temporary

**Definition.** `emplace_back(args...)` constructs the element in place
from `args`; `push_back(T{args...})` constructs a temporary and then
move-constructs the element from it.

**Use when.**

- The caller builds a temporary only to insert it:
  `v.push_back(T{a, b})` or `v.push_back(T(a))`.

**Do not use when.**

- The argument is already a `T`: `push_back(x)` and `emplace_back(x)`
  do the same copy. Measured: `COPIES emplace-back-lvalue: 1 -> 1`.
- The argument would call an `explicit` constructor by accident:
  `std::vector<std::vector<int>> v; v.emplace_back(10);` adds an inner
  vector of ten zeros, where `push_back(10)` does not compile.
- The argument is a raw owning pointer:
  `std::vector<std::unique_ptr<T>> v; v.emplace_back(new T);` leaks if
  the reallocation throws. Use `std::make_unique`.

**Example.**

```cpp
for (int i = 0; i < n; ++i) v.emplace_back(i);
// baseline: for (int i = 0; i < n; ++i) v.push_back(Item{i});
```

Runnable: `assets/examples/constructs/objects.cpp`.

**Cost removed.** One move and one destruction per element. Measured:
`MOVES emplace-back: 64 -> 0`.

**Verify.**

1. `verify.sh verify` compares the vectors and prints both
   `emplace-back` lines.
1. Review each converted call for the explicit-constructor hazard above.

## make_shared instead of shared_ptr from new

**Definition.** `std::make_shared<T>(args...)` allocates the control
block and the object together; the standard says "Implementations
should perform no more than one memory allocation"
([util.smartptr.shared.create]). `std::shared_ptr<T>(new T(...))`
performs two.

**Use when.**

- A hot path creates objects owned by `shared_ptr`
  (`shared_ptr<T>(new T...)` in a loop or per request).

**Do not use when.**

- `weak_ptr`s outlive the last `shared_ptr` and `T` is large: the
  single block (object storage included) stays allocated until the last
  `weak_ptr` is gone.
- A custom deleter is needed: `make_shared` cannot take one.

**Example.**

```cpp
std::shared_ptr<Node> shared_make(long v) {
  return std::make_shared<Node>(v);
}
// baseline: return std::shared_ptr<Node>(new Node(v));
```

Runnable: `assets/examples/constructs/objects.cpp`.

**Cost removed.** One allocation per object. Measured:
`ALLOC make-shared: 2 -> 1`; time 40.4 -> 23.5 ns.

**Verify.**

1. `verify.sh verify` compares the values and prints `ALLOC`.
1. `rg -n 'shared_ptr<[^>]+>\(new ' src/` lists the remaining sites.

## unique_ptr instead of shared_ptr

**Definition.** `std::unique_ptr<T>` is a single owning pointer (8 bytes
here) whose move is a pointer copy plus a null store;
`std::shared_ptr<T>` is two pointers (16 bytes) plus a control block
whose use count is updated with atomic read-modify-write instructions on
every copy and destruction.

**Use when.**

- Ownership is never shared: exactly one owner at any time, handed off
  by move. Run `rg -n 'shared_ptr' src/` and check whether any copy of
  the pointer outlives the original owner.

**Do not use when.**

- Ownership is genuinely shared (caches, graph nodes with several
  parents, callbacks on other threads).
- A public API returns `shared_ptr` and changing it is out of scope.

**Example.**

```cpp
void unique_handoff_candidate(std::unique_ptr<long> &p,
                              std::unique_ptr<long> *out) {
  *out = std::move(p); // no atomics
}
// baseline: *out = p; with std::shared_ptr<long> (ldadd)
```

Runnable: `assets/examples/constructs/objects.cpp`.

**Cost removed.** Atomic increments and decrements, and 8 bytes per
handle. Measured: `SIZE shared-vs-unique: sizeof shared_ptr 16, unique_ptr
8`; `ASM shared_handoff_baseline: 2 line(s) match` the atomic pattern,
`unique_handoff_candidate: 0`.

**Verify.**

1. `verify.sh verify` checks the value after handoff and that the
   source `unique_ptr` is null.
1. `verify.sh asm` asserts atomics present in the baseline and absent
   in the candidate.

## Pass shared_ptr by const reference

**Definition.** Passing `std::shared_ptr<T>` by value copies it: an
atomic increment (`ldadd`, relaxed) at the call and one atomic decrement
with acquire-release ordering (`ldaddal`) when the parameter dies. A
`shared_ptr<T> const&` or `T&` parameter does neither.

**Use when.**

- The callee uses the object only during the call and keeps no copy of
  the pointer.

**Do not use when.**

- The callee stores the pointer: take it by value and move it in.
- The caller's `shared_ptr` might be reset during the call (for
  example, the callee triggers a callback that clears the owner): the
  reference then dangles. Keep a local copy in that case.

**Example.**

```cpp
long read_by_ref(std::shared_ptr<long> const &p) { return *p; }
// baseline: long read_by_value(std::shared_ptr<long> p) { return *p; }
```

Runnable: `assets/examples/constructs/objects.cpp`.

**Cost removed.** Two atomic read-modify-writes per call. Measured:
`ASM shared_by_value_baseline: 2 line(s)` (`ldadd`, `ldaddal`),
`shared_by_ref_candidate: 0`; time for 1000 calls 13.9 -> 0.98 µs
(single thread; contention across threads makes the baseline worse).

**Verify.**

1. `verify.sh verify` checks equal sums and `use_count() == 1` afterward.
1. `verify.sh asm` asserts the atomic pattern.

[p0135]: https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2016/p0135r1.html
[dcl.init.general]: https://eel.is/c++draft/dcl.init.general
[class.copy.elision]: https://eel.is/c++draft/class.copy.elision
[expr.prim.id.unqual]: https://eel.is/c++draft/expr.prim.id.unqual
[p1825]: https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2019/p1825r0.html
[p2266]: https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2022/p2266r3.html
[vector.modifiers]: https://eel.is/c++draft/vector.modifiers
[util.smartptr.shared.create]: https://eel.is/c++draft/util.smartptr.shared.create
[tidy-copy]: https://clang.llvm.org/extra/clang-tidy/checks/performance/unnecessary-copy-initialization.html
