# Object shape and collection constructs

Baseline and candidate pairs live in
[`shapes.mjs`](../assets/examples/constructs/shapes.mjs); engine-internal
evidence is in `v8-probes.mjs` (node) and `jsc-probes.mjs` (bun).

Local numbers are machine-specific: Apple M1 Max, macOS arm64, node 26.8.2,
bun 1.4.2, medians from `sh assets/examples/verify.sh measure` (each side in
its own process) or from `verify` output lines.

## Contents

- Initialize every field in the constructor
- Assign undefined instead of delete
- Monomorphic call sites
- Packed arrays instead of holey arrays
- One elements kind per array
- Typed arrays for numeric records
- Map for dynamic keys
- Set for repeated membership tests

## Initialize every field in the constructor

**Definition.** V8 gives objects "with the same structure (same properties
in the same order)" the same hidden class and links classes through a
transition tree ([fast properties](https://v8.dev/blog/fast-properties));
JavaScriptCore does the same with structures. Assigning every field, in
one order, in one constructor makes all instances share one shape.

**Use when.**

- Objects of one logical type are built in several places or with
  conditional field order (`if (a) o.x = 1; o.y = 2; ...`).
- A hot function reads fields of those objects (see the next cards).

**Do not use when.**

- Objects are built once and read rarely: construction can get slower
  (measured below) with no read-side gain.
- Code relies on a field being absent (`"x" in o`, `Object.keys(o)`);
  initializing it to `undefined` changes those results.

**Example.**

```javascript
export class Point {
  constructor(x, y) {
    this.x = x; // same fields, same order, every time
    this.y = y;
  }
}
export const candidateRecords = (values) =>
  values.map((value, index) => new Point(value, index));
```

Runnable: `baselineRecords` / `candidateRecords` in `shapes.mjs`.

**Cost removed.** Shape divergence at read sites. Evidence: `%HaveSameMap`
is false across baseline records and true across candidate records
(V8); JSC structure IDs differ vs match. Local construction cost went up:
node 32.9 → 37.2 ns, bun 56.8 → 78.3 ns for 4 records, so the benefit
must come from reads (see Monomorphic call sites).

**Verify.**

1. `sh assets/examples/verify.sh verify`: `constructor-init` sums match
   for every input of length 0-4 over `[-1, 0, 2.5]`.
1. `v8-probes.mjs` and `jsc-probes.mjs` assert same-shape results; then
   measure the consuming hot loop, not only construction.

## Assign undefined instead of delete

**Definition.** `delete o.p` removes an own property
([ECMA-262 delete](https://tc39.es/ecma262/#sec-delete-operator)). V8 may
move objects with many adds and deletes to dictionary (slow) properties
([fast properties](https://v8.dev/blog/fast-properties)); locally, a single
`delete` of the last-added field already made `%HasFastProperties` false.
Assigning `undefined` keeps the property and the shape.

**Use when.**

- Some paths clear a field of a hot object type (`delete
  session.token`) and readers only test the value (`o.p === undefined`).

**Do not use when.**

- Consumers use `"p" in o`, `Object.hasOwn`, `Object.keys`, spread, or
  `for...in`: the property still exists after assigning `undefined`.
- The object is a dictionary of dynamic keys: use a `Map` instead.

**Example.**

```javascript
export function candidateClear(session) {
  session.token = undefined; // property stays; shape stays
  return session;
}
```

Runnable: `baselineClear` / `candidateClear` in `shapes.mjs`.

**Cost removed.** Dictionary-mode transition on V8
(`%HasFastProperties` false → true) and a `PropertyDeletion` structure
transition on JSC. `JSON.stringify` output is identical because it skips
`undefined` values.

**Verify.**

1. `verify` checks equal values and equal `JSON.stringify` output, and
   records that `"token" in o` differs (false vs true), so audit callers
   for `in`/`hasOwn`/`keys` first: `rg -n '"token" in|hasOwn|keys\('`.
1. `v8-probes.mjs` asserts `%HasFastProperties` false for the baseline
   and true for the candidate.

## Monomorphic call sites

**Definition.** Inline caches at a property access remember the shapes
they have seen. V8 tracks up to `--max-valid-polymorphic-map-count` shapes
(default 4, from `node --v8-options` on node 26.8.2); beyond that the site
is megamorphic and uses a slower generic lookup. Feeding one shape keeps
the site monomorphic.

**Use when.**

- A hot function reads the same fields from objects built in different
  places (object literals in different key orders, optional extra fields).
- `%HaveSameMap` or JSC structure IDs show more than one shape at the site.

**Do not use when.**

- Unifying shapes requires copying objects on every call: that
  allocation costs more than the lookup (measured below).
- A CPU profile does not show the site as hot.

**Example.**

```javascript
// Create the shape once where data enters, not inside the hot path.
const points = rows.map((r) => new Point(r.x, r.y));
let total = 0;
for (const p of points) total += p.x * p.x + p.y * p.y;
```

Runnable: `mixedShapes`, `baselineTotal`, `candidateTotal` in `shapes.mjs`.

**Cost removed.** Megamorphic property lookups. Local (256 points, 5 shapes
vs 1): node 2,991.0 → 445.7 ns; bun 1,091.6 → 739.0 ns. Normalizing inside
each call instead: node 3,007.7 → 3,187.6 ns, bun 983.9 → 3,917.6 ns
(slower on both).

**Verify.**

1. `verify` checks `baselineTotal(mixed) === candidateTotal(mixed)` for
   inputs of length 0-4; `v8-probes.mjs` asserts 5 distinct maps for the
   mixed input and 1 after normalization.
1. `BENCH_FILTER=monomorphic sh assets/examples/verify.sh measure`.

## Packed arrays instead of holey arrays

**Definition.** V8 tracks an elements kind per array. "Creating holes in
the array ... downgrades the elements kind to its 'holey' variant", and
"once a hole is created in an array, it's marked as holey forever"
([elements kinds](https://v8.dev/blog/elements-kinds)). `new Array(n)`
starts holey; `[]` plus `push`, array literals, and `Array.from` stay
packed. The post's 2025-02-28 update makes `Array.prototype.fill` an
exception: locally `%HasHoleyElements(new Array(8).fill(0))` is false on
node 26.8.2.

**Use when.**

- Arrays are preallocated with `new Array(n)` or written out of order and
  later read by hot loops or passed to builtins.

**Do not use when.**

- Only construction speed matters: preallocation built faster locally
  (below).
- The code depends on holes (`i in arr`, `forEach`/`map` skipping holes);
  a packed array has `undefined` values instead, which those APIs visit.
- The rows would be built with `new Array(n).fill({})`:
  every slot is the same object. Use `Array.from({ length: n }, () =>
  ({}))` for independent rows.

**Example.**

```javascript
export function candidateSquares(n) {
  const out = []; // PACKED_SMI_ELEMENTS; push keeps it packed
  for (let i = 0; i < n; i++) out.push(i * i);
  return out;
}
```

Runnable: `baselineSquares` / `candidateSquares` in `shapes.mjs`. When
construction speed matters, `new Array(n).fill(0)` followed by indexed
writes keeps preallocation and a packed kind on V8 (probe above).

**Cost removed.** Hole checks and prototype-chain lookups on reads of
holey arrays, per the V8 post. Local timing did not show it for an
in-bounds indexed sum over 4,096 elements (node 7,722.8 vs 7,698.2 ns;
bun 2,524.7 vs 2,533.3 ns), and building 256 elements was slower with
`push` (node 314.4 → 753.3 ns; bun 490.6 → 1,179.6 ns). Apply it only
where a profile of the reading code improves.

**Verify.**

1. `verify` checks equal contents for n = 0, 1, 7, records that
   `0 in new Array(3).map(...)` is false (holes are skipped), and asserts
   the shared-object hazard of `fill({})`.
1. `v8-probes.mjs` asserts `%HasHoleyElements` true → false; then
   `BENCH_FILTER=packed-array sh assets/examples/verify.sh measure`.

## One elements kind per array

**Definition.** Elements kinds move only "from specific kinds to more
general kinds": SMI → DOUBLE → generic ELEMENTS. "just adding -0 to an
array of small integers is enough to transition it to
PACKED_DOUBLE_ELEMENTS", and `NaN`/`Infinity` do the same
([elements kinds](https://v8.dev/blog/elements-kinds)). Mixing `null` or
strings into a numeric array makes it generic for its lifetime.

**Use when.**

- A numeric array also stores sentinels (`null`, `undefined`, `""`) for
  missing values, and a hot loop does arithmetic on it.

**Do not use when.**

- The array is small or cold: the split representation adds code.
- Callers need the mixed array itself: converting back costs a copy.

**Example.**

```javascript
export function candidateReadings(raw) {
  const values = new Float64Array(raw.length);
  const present = new Uint8Array(raw.length); // replaces null sentinels
  for (let i = 0; i < raw.length; i++) {
    if (raw[i] !== "") {
      values[i] = Number(raw[i]);
      present[i] = 1;
    }
  }
  return { values, present };
}
```

Runnable: `baselineReadings` / `candidateReadings` in `shapes.mjs`.

**Cost removed.** Generic (boxed) elements in a numeric array. Evidence:
`%HasObjectElements` is true for the baseline's `[1, null, 2]` shape;
`%HasDoubleElements` becomes true after `push(-0)` onto `[1, 2, 3]`. No
timing claim is made locally; measure the consuming loop.

**Verify.**

1. `verify` checks `readingsAsArray(candidate)` equals the baseline for all
   inputs of length 0-4 (missing, negative, fractional values).
1. `v8-probes.mjs` asserts the elements-kind transitions above.

## Typed arrays for numeric records

**Definition.** `Float64Array` and friends store raw numbers in an
`ArrayBuffer` outside the object heap; element writes coerce with
`ToNumber` (or wrap/clamp for integer types). A structure of arrays
(`x[]`, `v[]`) replaces an array of small objects.

**Use when.**

- Hot loops create and scan many records of numeric fields (particles,
  coordinates, matrices, histograms).

**Do not use when.**

- Fields can be non-numbers: `new Float64Array(["1", {}])` is `[1, NaN]`,
  silently.
- Integer fields exceed the element type (`Int32Array` wraps, `Uint8Array`
  wraps, `Uint8ClampedArray` clamps).
- Records are few or need identity, methods, or optional fields.

**Example.**

```javascript
export function candidateParticles(n) {
  const x = new Float64Array(n);
  const v = new Float64Array(n);
  for (let i = 0; i < n; i++) {
    x[i] = i * 0.5;
    v[i] = i * 1.5;
  }
  for (let i = 0; i < n; i++) x[i] += v[i];
  return { x, v };
}
```

Runnable: `baselineParticles` / `candidateParticles` in `shapes.mjs`.

**Cost removed.** Per-record objects and boxed doubles. Local (node, 2,000
records, heap + ArrayBuffer bytes): 180,954 → 32,454 B/call. Time for 256
records: node 1,732.8 → 1,053.8 ns; bun 2,558.9 → 781.5 ns.

**Verify.**

1. `verify` compares positions for n = 5 and asserts the coercion case.
1. `ALLOC typed-array` line in `verify` output (node); then
   `BENCH_FILTER=typed-array sh assets/examples/verify.sh measure`.

## Map for dynamic keys

**Definition.** `Map` stores arbitrary keys in insertion order with no
inherited keys. MDN's comparison lists Map as performing "better in
scenarios involving frequent additions and removals of key-value pairs"
([Objects vs. Maps][objects-vs-maps]).
An object used as a dictionary also inherits `constructor`, `toString`,
and `__proto__` handling from `Object.prototype`.

**Use when.**

- Keys come from data (user input, IDs, words) and the set of keys grows
  or shrinks at run time.
- Keys can collide with `Object.prototype` names, or are not strings.

**Do not use when.**

- The key set is fixed and known (a record): use an object or a class.
- The result is serialized with `JSON.stringify`: a `Map` serializes to
  `{}`; convert with `Object.fromEntries` at the boundary.
- The project ships on bun and no bun measurement supports the switch:
  locally the Map version was slower on bun (below).

**Example.**

```javascript
export function candidateCounts(words) {
  const counts = new Map();
  for (const w of words) counts.set(w, (counts.get(w) ?? 0) + 1);
  return counts;
}
```

Runnable: `baselineCounts` / `candidateCounts` in `shapes.mjs`.

**Cost removed.** Dictionary-mode objects and prototype-key bugs. The
baseline `{}` counter turns `counts.constructor` into a string
(`"function Object() { [native code] }1"`) and orders integer-like keys
first. Local (256 words, 97 distinct): node 7,901.1 → 5,215.5 ns; bun
2,512.7 → 6,463.0 ns. The direction depends on the runtime.

**Verify.**

1. `verify` checks Map entries and order for words including
   `"__proto__"`, `"constructor"`, `"10"`, `"2"`, and records the object's
   integer-first key order.
1. `v8-probes.mjs`/`jsc-probes.mjs` show the object-as-dictionary is in
   dictionary mode; `BENCH_FILTER=map-counts ... measure` on each target.

## Set for repeated membership tests

**Definition.** `Set.prototype.has` is a hash lookup, while
`Array.prototype.includes` scans linearly. Building a `Set` once turns m
queries over n items from O(n·m) comparisons into O(n + m). Both
`includes` and `Set` use SameValueZero (`NaN` matches); `indexOf` uses
strict equality (`NaN` never matches).

**Use when.**

- A loop calls `includes`/`indexOf`/`some(x => x === q)` on the same array
  many times.

**Do not use when.**

- The array is tiny or queried once: building the set costs more than
  the scans.
- The code relied on `indexOf` not finding `NaN`; `Set.has(NaN)` is true.

**Example.**

```javascript
export function candidateKnown(allowed, queries) {
  const set = new Set(allowed); // built once per call, O(n)
  return queries.filter((q) => set.has(q));
}
```

Runnable: `baselineKnown` / `candidateKnown` in `shapes.mjs`.

**Cost removed.** Linear scans. Local `sh assets/examples/verify.sh
verify` runs (20,000 keys, 2,000 queries; varies between runs): node
181.85-204.17 → 1.11-1.19 ms; bun 42.03-109.03 → 1.66-1.97 ms.

**Verify.**

1. `verify` compares both functions on every allowed-list of length 0-3
   over `["a", "b", NaN]` and on the large input.
1. `verify` asserts the candidate is at least 3x faster on the large input
   (`TIME set-membership` line).

[objects-vs-maps]:
  https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Map#objects_vs._maps
