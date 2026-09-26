# Allocation, iteration, string, and regex constructs

Baseline and candidate pairs live in
[`allocation.mjs`](../assets/examples/constructs/allocation.mjs);
`verify()` there proves equivalence and asserts the allocation drop with
the heap oracle from [measurement](measurement.md).

Local numbers are machine-specific: Apple M1 Max, macOS arm64, node 26.8.2,
bun 1.4.2. `B/call` values come from `ALLOC` lines of
`sh assets/examples/verify.sh verify` (node only); ns values are medians
from `sh assets/examples/verify.sh measure`.

## Contents

- Fuse map/filter/reduce chains into one loop
- Hoist closures out of hot calls
- Indexed for loop instead of forEach
- push instead of concat in a loop
- String += instead of array join
- Hoist regular-expression literals
- Cache RegExp objects built from strings
- Sticky regex for positional tokenizing
- Copy the changed path instead of deep cloning
- structuredClone instead of a JSON round trip
- try/catch inside hot functions

## Fuse map/filter/reduce chains into one loop

**Definition.** Each `filter` or `map` in a chain allocates a new array for
its result; a single loop computes the same value with no intermediate
arrays and no per-element callback calls.

**Use when.**

- A chain of `filter`/`map`/`slice` feeds a `reduce`, `length`, or a
  single consumer inside a hot path.

**Do not use when.**

- The intermediate array is used elsewhere or returned.
- The input can be sparse and the chain's hole-skipping matters: the
  loop reads holes as `undefined`.
- The path is cold: the loop costs readability for no measured gain.

**Example.**

```javascript
export function candidateEvenSquares(values) {
  let sum = 0;
  for (let i = 0; i < values.length; i++) {
    const v = values[i];
    if (v % 2 === 0) sum += v * v;
  }
  return sum;
}
```

Runnable: `baselineEvenSquares` / `candidateEvenSquares` in `allocation.mjs`.

**Cost removed.** Two intermediate arrays per call. Local (64 numbers):
1,033 → 1 B/call; node 190.8 → 53.5 ns; bun 279.5 → 72.9 ns.

**Verify.**

1. `verify` compares both on every array of length 0-4 over
   `[-2, 0, 1, 3]` (negative, zero, odd, even).
1. `ALLOC fuse-chain` line must show the drop; the heap oracle asserts the
   candidate uses at most 10% of the baseline.

## Hoist closures out of hot calls

**Definition.** Every evaluation of an arrow function or function
expression creates a new function object, plus a context object when it
captures variables. Inlining the predicate (or hoisting a non-capturing
function to module scope) removes that allocation.

**Use when.**

- A hot call passes a fresh capturing callback to a helper each time
  (`countIf(values, (v) => v > t)`), and a CPU or allocation profile
  shows the call.

**Do not use when.**

- The callback is created once per request or at setup.
- The callback is part of a public API: keep the API and optimize inside.

**Example.**

```javascript
export function candidateAbove(values, t) {
  let count = 0;
  for (let i = 0; i < values.length; i++) if (values[i] > t) count++;
  return count;
}
```

Runnable: `baselineAbove` / `candidateAbove` in `allocation.mjs`.

**Cost removed.** One closure (and context) per call: local 97 → 1
B/call on node 26.8.2 even when the helper was inlined: escape analysis
did not remove it. Time barely moved: node 41.7 → 41.4 ns, bun 79.2 → 71.4
ns. Apply it for GC pressure, not speed.

**Verify.**

1. `verify` compares both for every input of length 0-4 with t = 0.
1. `ALLOC hoist-closure` line; the oracle requires <= 10% of the baseline.

## Indexed for loop instead of forEach

**Definition.** `forEach` calls a callback per present element and skips
holes; an indexed `for` loop runs inline and visits every index. V8's team
writes that "the performance of both for-of and forEach is on par with the
old-fashioned for loop"
([elements kinds](https://v8.dev/blog/elements-kinds#performance-tips));
measure before changing.

**Use when.**

- A CPU profile shows a hot `forEach` callback and a local measurement of
  the rewrite on the target runtime shows a gain.

**Do not use when.**

- The array can have holes: the results differ (`[1, , 3]` sums to 4 with
  `forEach` and `NaN` with the loop).
- There is no measurement: per the V8 statement above, expect no gain
  in general.

**Example.**

```javascript
export function forLoopSum(values) {
  let sum = 0;
  for (let i = 0; i < values.length; i++) sum += values[i];
  return sum;
}
```

Runnable: `forEachSum` / `forLoopSum` in `allocation.mjs`.

**Cost removed.** Callback invocation per element when the engine does not
inline it. Local (64 numbers): node 193.6 → 42.0 ns (baseline min 120.3,
so noisy), bun 88.8 → 53.3 ns. This contradicts the V8 statement for
this case; the direction may differ on other inputs and machines.

**Verify.**

1. `verify` compares sums on dense inputs and asserts the documented
   difference on `[1, , 3]`.
1. `BENCH_FILTER=for-loop sh assets/examples/verify.sh measure`.

## push instead of concat in a loop

**Definition.** `out = out.concat([v])` copies the whole array on every
iteration (O(n²) element copies); `out.push(v)` appends in amortized O(1).

**Use when.**

- A loop grows an array with `concat` or with spread (`[...out, v]`).

**Do not use when.**

- Other code holds a reference to the old array and must not observe the
  new elements (immutability contract): copy once at the end instead.

**Example.**

```javascript
export function candidateCollect(values) {
  const out = [];
  for (const v of values) out.push(v);
  return out;
}
```

Runnable: `baselineCollect` / `candidateCollect` in `allocation.mjs`.

**Cost removed.** n full-array copies. Local (64 values): 2,535-3,042 →
1,217 B/call (the remainder is the result array); node 8,291.9 → 162.2
ns; bun 3,141.8 → 330.8 ns.

**Verify.**

1. `verify` compares results for all inputs of length 0-4 and for nested
   arrays (`concat([v])` keeps `v` nested, as `push(v)` does).
1. `ALLOC push-not-concat` line; the oracle requires <= 50%.

## String += instead of array join

**Definition.** In V8, `a + b` on strings of combined length >= 13 builds
a `ConsString`, "a pair where the first and second components are
pointers to other string values"; the tree is flattened when the
characters are needed
([string.h](https://github.com/v8/v8/blob/main/src/objects/string.h),
`ConsString::kMinLength = 13`). JSC also builds ropes (`isRope` in
`bun:jsc`). So `+=` in a loop does not copy the prefix each time.

**Use when.**

- Code pushes pieces into an array only to `join` them, on the belief
  that `+=` is quadratic.

**Do not use when.**

- Pieces are already in an array: `join` is one call.
- The string is indexed character by character while it is being built:
  each read flattens the rope.
- The target engine is neither V8 nor JSC and was not measured.

**Example.**

```javascript
export function concatCsv(words) {
  let out = "";
  for (let i = 0; i < words.length; i++) {
    if (i > 0) out += ",";
    out += words[i];
  }
  return out;
}
```

Runnable: `joinCsv` / `concatCsv` in `allocation.mjs`.

**Cost removed.** The pieces array and its growth. Local (200 words): node
3,326.4 → 1,459.4 ns; bun 2,991.1 → 2,058.5 ns. Allocation deltas for this
pair varied between runs on node (JIT tier dependent), so no byte claim.

**Verify.**

1. `verify` compares both on every word list of length 0-4.
1. `v8-probes.mjs` asserts `%StringIsFlat` is false after building and
   true after `charCodeAt`; `jsc-probes.mjs` asserts `isRope` true then
   false. Then `BENCH_FILTER=string ... measure`.

## Hoist regular-expression literals

**Definition.** "A regular expression literal is an input element that is
converted to a RegExp object ... each time the literal is evaluated"
([ECMA-262 12.9.5][ecma-262-12-9-5]).
A literal in a function body allocates a RegExp object per call; a module
constant is created once.

**Use when.**

- A hot function contains a regex literal without the `g` or `y` flag.

**Do not use when.**

- The regex has `g` or `y`: `test`/`exec` read and write `lastIndex`, so a
  shared instance carries state between calls (`/a/g` tested twice on `"a"`
  gives `true` then `false`). Reset `lastIndex = 0` before each use or
  keep it local.

**Example.**

```javascript
const ID = /^[a-z][a-z0-9_]{0,31}$/; // no g/y flag: no lastIndex state
export const candidateIsId = (s) => ID.test(s);
```

Runnable: `baselineIsId` / `candidateIsId` in `allocation.mjs`.

**Cost removed.** One RegExp object per call: local 57 → 1 B/call;
node 21.5 → 17.5 ns; bun 16.4 → 13.6 ns.

**Verify.**

1. `verify` compares results on empty, boundary-length (32, 33), leading
   digit, uppercase, and trailing-newline inputs, and asserts the shared
   `/g` hazard.
1. `ALLOC hoist-regex` line; the oracle requires <= 50%.

## Cache RegExp objects built from strings

**Definition.** `new RegExp(source, flags)` parses and creates a RegExp
object on every call. A `Map` from source to RegExp reuses one instance
per distinct pattern.

**Use when.**

- Patterns are built from a small, bounded set of runtime strings
  (configured words, column names) in a hot path.

**Do not use when.**

- Keys are unbounded (user input): the cache grows without limit; bound
  it (LRU) or do not cache.
- The regex has `g` or `y` (shared `lastIndex`, as above).

**Example.**

```javascript
const wordCache = new Map(); // bounded: keys come from a fixed vocabulary
export function candidateHasWord(text, word) {
  let re = wordCache.get(word);
  if (re === undefined) {
    re = new RegExp(`\\b${escape(word)}\\b`, "u");
    wordCache.set(word, re);
  }
  return re.test(text);
}
```

Runnable: `baselineHasWord` / `candidateHasWord` in `allocation.mjs`.

**Cost removed.** Per-call RegExp construction and pattern string
building: local 176 → 1 B/call; node 187.6 → 22.3 ns; bun 46.9 → 38.2 ns
(mitata: bun 46.65 → 19.21 ns/iter).

**Verify.**

1. `verify` compares 4 words (including regex metacharacters and `é`)
   against 5 texts.
1. `ALLOC regex-cache` line; the oracle requires <= 50%.

## Sticky regex for positional tokenizing

**Definition.** With the `y` flag a regex "attempts to match the target
string only from the index indicated by the lastIndex property"
([MDN sticky][mdn-sticky]).
A tokenizer advances `lastIndex` instead of slicing the remaining input
and anchoring with `^`.

**Use when.**

- A lexer calls `re.exec(text.slice(pos))` with a `^`-anchored pattern.

**Do not use when.**

- The pattern starts with `^`: `^` still means start of input with `y`,
  so it would only match at 0.
- The rewrite uses `g` instead of the sticky flag: a global regex skips
  unmatched characters and silently drops garbage between tokens.
- The instance is shared across concurrent tokenizers (shared lastIndex).

**Example.**

```javascript
const TOKEN = /\s*(\w+|[^\s\w])/y;
export function stickyTokens(text) {
  const out = [];
  TOKEN.lastIndex = 0;
  while (TOKEN.lastIndex < text.length) {
    const m = TOKEN.exec(text); // matches only at lastIndex
    if (m === null) break;
    out.push(m[1]);
  }
  return out;
}
```

Runnable: `sliceTokens` / `stickyTokens` in `allocation.mjs`.

**Cost removed.** One substring per token. Local (460-char input): node
10,863.1 → 7,646.0 ns; bun 10,032.4 → 8,057.8 ns. No allocation assertion
is made: `SlicedString` substrings already share the parent's characters
in V8 ([string.h][string-h]), so the saving is per-token objects, not
copies. Measure on each target runtime and input size before adopting.

**Verify.**

1. `verify` compares token lists for `""`, whitespace-only, punctuation,
   `é!`, and the long input.
1. `BENCH_FILTER=sticky ... measure` on every target runtime.

## Copy the changed path instead of deep cloning

**Definition.** An immutable update copies only the objects on the path to
the changed field and shares every untouched subtree
(structural sharing), instead of cloning the whole state.

**Use when.**

- Code deep-clones state (`JSON.parse(JSON.stringify(s))`,
  `structuredClone(s)`, lodash `cloneDeep`) only to change a few fields.

**Do not use when.**

- Some consumer mutates the result in place: shared subtrees would then be
  mutated in the original too. Freeze or audit mutators first.
- The deep clone is needed to break aliasing with external mutable data.

**Example.**

```javascript
export function candidateBump(state, index) {
  const items = state.items.slice();
  items[index] = { ...items[index], qty: items[index].qty + 1 };
  return { ...state, items }; // untouched subtrees are shared
}
```

Runnable: `baselineBump` / `candidateBump` in `allocation.mjs`.

**Cost removed.** Serializing and rebuilding the whole tree. Local (50
items + nested user): 3,659 → 531 B/call; node 8,233.2 → 50.3 ns; bun
4,693.2 → 76.8 ns.

**Verify.**

1. `verify` compares with the JSON-clone baseline at the first and last
   index, checks `result.user === state.user`, and checks the input is not
   mutated.
1. `ALLOC copy-changed-path` line; the oracle requires <= 50%.

## structuredClone instead of a JSON round trip

**Definition.** [`structuredClone`][structuredclone] (a global since node
17.0.0, per [globals][node-globals]) deep-copies with the structured clone
algorithm: it keeps `undefined`, `NaN`, `Date`, `Map`, `Set`, typed
arrays, and cycles, and throws
`DataCloneError` for functions. `JSON.parse(JSON.stringify(x))` drops
`undefined` properties, turns `NaN` into `null`, `Date` into a string, and
`Set`/`Map` into `{}`.

**Use when.**

- A JSON round trip corrupts data and a deep copy is required (try the
  previous card first).

**Do not use when.**

- The goal is speed: locally `structuredClone` was slower and allocated
  more than the JSON round trip for plain data.
- The object has class instances whose prototype or getters matter: the
  clone is a plain object.

**Example.**

```javascript
const input = { missing: undefined, nan: NaN, when: new Date(0) };
const copy = structuredClone(input); // keeps all three
```

Runnable: `jsonCopy` / `structuredCopy` in `allocation.mjs`.

**Cost removed.** Data loss, not time. Local (the 50-item state): node
8,232.5 → 21,700.7 ns; bun 4,737.7 → 14,226.3 ns (slower on both).

**Verify.**

1. `verify` asserts the clone equals the input and records what JSON
   loses (`missing` absent, `nan` null, `when` string, `tags` `{}`).
1. `verify` asserts `DataCloneError` for an object with a method.

## try/catch inside hot functions

**Definition.** Crankshaft "was not designed to optimize JavaScript code
using ... try, catch, and finally"; TurboFan replaced it in V8 5.9
([launch post](https://v8.dev/blog/launching-ignition-and-turbofan)).
Current engines optimize functions that contain try/catch, so do not move
a try/catch for speed.

**Use when.**

- A code review proposes hoisting try/catch out of a loop, or moving the
  body into a helper, "because try/catch deoptimizes". Keep the per-item
  recovery the contract needs.

**Do not use when.**

- Exceptions are thrown on the hot path as control flow: throwing and
  unwinding still costs; return a status value instead.

**Example.**

```javascript
export function parseAllOrNull(lines) {
  const out = [];
  for (const line of lines) {
    try {
      out.push(JSON.parse(line)); // per-item recovery
    } catch {
      out.push(null);
    }
  }
  return out;
}
```

Runnable: `parseAllOrNull` / `parseAllOrThrow` in `allocation.mjs`.

**Cost removed.** A behavior-changing rewrite: hoisting the try makes one
bad line discard all results (`parseAllOrThrow` returns `null`).

**Verify.**

1. `verify` asserts `[{a: 1}, null, 2]` for the per-item version and
   `null` for the hoisted one.
1. `v8-probes.mjs` asserts `kTurboFanned` in `%GetOptimizationStatus`;
   `jsc-probes.mjs` asserts `numberOfDFGCompiles > 0` on bun.

[ecma-262-12-9-5]:
  https://tc39.es/ecma262/#sec-literals-regular-expression-literals
[mdn-sticky]:
  https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/RegExp/sticky
[structuredclone]:
  https://developer.mozilla.org/en-US/docs/Web/API/Window/structuredClone
[string-h]: https://github.com/v8/v8/blob/main/src/objects/string.h
[node-globals]: https://nodejs.org/api/globals.html
