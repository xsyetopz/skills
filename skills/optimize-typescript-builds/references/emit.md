# Emit constructs

Each card changes the JavaScript that `tsc` emits from a TypeScript source
construct. Baseline and candidate sources live in
[`assets/examples/emit/`](../assets/examples/emit); the oracle in
`emit-cases.ts` compiles both, runs them in fresh Node processes, compares
results, and asserts the emitted-code property the card names. Run
`sh assets/examples/verify.sh emit` from the project root.

Local numbers are machine-specific: Apple M1 Max, macOS, tsc 7.0.2, Node
26.8.2, Bun 1.4.2. Byte and helper counts are deterministic for a given tsc
version. Timings come from three `verify.sh measure` runs (each the median
of 7 repetitions after warmup) on a machine shared with other builds (load
average 23-41), so only order-of-magnitude gaps count as results.

Tier: Executed. `verify.sh emit` (oracles) and three `verify.sh measure`
runs (timings) with tsc 7.0.2, Node 26.8.2, and Bun 1.4.2.

## Contents

- Const enum
- Const enum under isolatedModules
- As const object instead of enum
- Explicit fields instead of parameter properties
- Declare for redeclared fields
- ES module instead of namespace
- Native async functions from ES2017
- Native private fields from ES2022
- Native object spread from ES2018
- importHelpers with tslib
- Standard decorators and the target
- Decorator metadata retains imports
- Top-level import type

## Const enum

**Definition.** `const enum` members are replaced by their literal values
at each use site (`0 /* Op.Add */`) and the declaration emits no code, when
`tsc` compiles the whole program without `isolatedModules`
([enums handbook][enums]).

**Use when.**

- A regular `enum` is used only for member access, in code that `tsc`
  itself emits (not a Babel/esbuild/Bun single-file pipeline).
- The project does not set `isolatedModules`, `verbatimModuleSyntax`, or
  `erasableSyntaxOnly`.

**Do not use when.**

- Any of those flags is set: the literal inlining disappears (see
  [Const enum under isolatedModules](#const-enum-under-isolatedmodules)).
- Callers iterate the enum or read reverse mappings (`Op[0] === "Add"`):
  there is no runtime object.
- The enum is exported from a published `.d.ts`: consumers compiled with
  `isolatedModules` cannot inline it ([enums handbook][enums], "Const enum
  pitfalls").
- The code must run under Node type stripping: enums are rejected with
  `ERR_UNSUPPORTED_TYPESCRIPT_SYNTAX` ([Node TypeScript][node-ts]).

**Example.**

```typescript
const enum Op {
  Add,
  Sub,
  Mul,
}

export function run(n: number): number {
  let sum = 0;
  for (let i = 0; i < n; i++) {
    const op = i % 3;
    sum += op === Op.Add ? 1 : op === Op.Sub ? 2 : op === Op.Mul ? 3 : 0;
  }
  return sum;
}
```

Emitted at `--target es2022` (baseline `enum` first, then `const enum`):

```javascript
var Op;
(function (Op) {
    Op[Op["Add"] = 0] = "Add";
    Op[Op["Sub"] = 1] = "Sub";
    Op[Op["Mul"] = 2] = "Mul";
})(Op || (Op = {}));
// const enum: no declaration; uses become
// op === 0 /* Op.Add */ ? 1 : op === 1 /* Op.Sub */ ? 2 : ...
```

Runnable: `emit/enum/regular.ts` and `emit/enum/const.ts`.

**Cost removed.** The enum IIFE and its two-way object, plus a property
load per use. Local: emitted file 415 B to 228 B. Runtime at `n = 1e8`,
three shared-machine runs: Node 189-196 ms vs 156-165 ms (small but
consistent); Bun 130-147 ms vs 130-166 ms (no consistent difference).
Expect size savings and at most a small speed change; measure it in your
own hot loop.

**Verify.**

1. Behavior: `sh assets/examples/verify.sh emit` compares `run(3000)` for
   `regular.js`, `const.js`, and `as-const.js`.
1. Benefit: the same run asserts `const.js` has no `(function (Op)` IIFE,
   contains `0 /* Op.Add */`, and prints
   `METRIC const-enum emitted bytes: 415 -> 228`.

## Const enum under isolatedModules

**Definition.** `isolatedModules` makes `preserveConstEnums` default to
`true` ([tsconfig preserveConstEnums][tsc-preserve]), so the const enum
object is emitted. With tsc 7.0.2 the references are also left as property
reads (`Op.Add`, `Level.High`), both within the same file and across files;
this was observed locally, not found in the documentation.

**Use when.**

- Deciding whether converting enums to `const enum` shrinks output in a
  project that sets `isolatedModules` or `verbatimModuleSyntax` (which
  requires the same single-file safety).

**Do not use when.**

- Expecting inlining: under these flags the conversion removes nothing, and
  tools that transpile one file at a time (`bun build --no-bundle`,
  esbuild) never see another file's const enum values.

**Example.**

```typescript
// levels.ts
export const enum Level {
  Low = 1,
  High = 2,
}
// use-levels.ts
import { Level } from "./levels.ts";
export function run(n: number): number {
  return n > 10 ? Level.High : Level.Low;
}
```

Runnable: `emit/enum/levels.ts`, `emit/enum/use-levels.ts`. Without
`isolatedModules`, `use-levels.js` contains `2 /* Level.High */` and
`levels.js` is empty; with it, `use-levels.js` keeps
`import { Level } from "./levels.js"` and `Level.High`.

**Cost removed.** None; this card prevents a no-op change. Check with
`grep -c "Level.High" out/use-levels.js` after compiling each way.

**Verify.**

1. Behavior: the oracle runs the `isolatedModules` build and checks
   `run(20) === 2`.
1. Benefit check (negative): on tsc 7+ the oracle asserts `Op.Add` and
   `Level.High` remain in the output; on older tsc it prints `SKIP` for the
   inlining check. Re-run it on your tsc before relying on the result.

## As const object instead of enum

**Definition.** A `const` object literal with `as const` plus
`type Op = (typeof Op)[keyof typeof Op]` gives named constants and a union
of their literal types using only erasable syntax
([TypeScript 5.8 erasableSyntaxOnly][ts58]).

**Use when.**

- The code runs under Node type stripping or must pass
  `erasableSyntaxOnly`.
- Callers need a runtime object (iteration with `Object.values`) but not
  reverse mappings.

**Do not use when.**

- Callers rely on reverse mapping (`Op[0]`) or on nominal enum typing
  (assigning `0` to a parameter of enum type is an error for enums but not
  for the literal union).
- A published API exposes the enum type: changing it is a breaking change.

**Example.**

```typescript
const Op = { Add: 0, Sub: 1, Mul: 2 } as const;
type Op = (typeof Op)[keyof typeof Op];

export function isOp(value: number): value is Op {
  return value === Op.Add || value === Op.Sub || value === Op.Mul;
}
```

Runnable: `emit/enum/as-const.ts`. Emitted JavaScript is the object
literal only.

**Cost removed.** The enum IIFE and the need for a build step: Node runs
the file directly, while the `enum` baseline fails with
`ERR_UNSUPPORTED_TYPESCRIPT_SYNTAX`. Runtime at `n = 1e8` (one run of the
final fixture, shared machine): Node 192 ms vs 155 ms, Bun 130 ms vs
130 ms: not enough to claim a speedup.

**Verify.**

1. Behavior: the oracle compares `as-const.js` and the directly executed
   `as-const.ts` with the enum baseline on `run(3000)`.
1. Benefit: `tsc --noEmit --erasableSyntaxOnly` reports `TS1294` for
   `regular.ts` and passes for `as-const.ts`; `node call.ts
   emit/enum/regular.ts 30` fails with `ERR_UNSUPPORTED_TYPESCRIPT_SYNTAX`.

## Explicit fields instead of parameter properties

**Definition.** A parameter property (`constructor(public x: number)`)
makes `tsc` generate a field and a `this.x = x` assignment; writing the
field and assignment by hand produces the same JavaScript without
non-erasable syntax ([classes handbook][classes]).

**Use when.**

- The project adopts `erasableSyntaxOnly` or runs `.ts` files with Node
  type stripping, which rejects parameter properties
  ([Node TypeScript][node-ts]).

**Do not use when.**

- The goal is runtime speed: at `--target es2022` both forms emit `x;`
  field declarations plus constructor assignments.

**Example.**

```typescript
export class Point {
  readonly x: number;
  readonly y: number;
  constructor(x: number, y: number) {
    this.x = x;
    this.y = y;
  }
}
```

Runnable: `emit/class/fields.ts` (candidate) and
`emit/class/param-props.ts` (baseline).

**Cost removed.** A build step for this file (Node runs it directly) and
one `TS1294` per parameter property under `erasableSyntaxOnly`. Runtime:
no stable direction for `1e7` constructions across three runs (Node
63-119 ms vs 62-90 ms, Bun 9.9-10.4 ms vs 10.0-15.3 ms).

**Verify.**

1. Behavior: the oracle compares `run(50)` for both compiled files and for
   `fields.ts` executed directly by Node.
1. Benefit: `TS1294` for the baseline and none for the candidate under
   `erasableSyntaxOnly`; Node rejects the baseline `.ts` with
   `ERR_UNSUPPORTED_TYPESCRIPT_SYNTAX`.

## Declare for redeclared fields

**Definition.** With `useDefineForClassFields` (default `true` when
`target` is ES2022 or later), a subclass field declaration without an
initializer re-defines the property as `undefined` after `super()` returns;
`declare resident: Dog` narrows the type and emits nothing
([classes handbook][classes], [useDefineForClassFields][tsc-udfcf]).

**Use when.**

- A subclass redeclares an inherited property only to narrow its type.
- The target moves to ES2022+ or a single-file transpiler compiles the
  class.

**Do not use when.**

- The subclass needs its own initialized field: give it an initializer
  instead.

**Example.**

```typescript
class House {
  resident: Animal;
  constructor(animal: Animal) {
    this.resident = animal;
  }
}

class DogHouse extends House {
  declare resident: Dog;
}
```

Runnable: `emit/class/declare-field.ts`; the hazard is
`emit/class/redeclare.ts` (`resident!: Dog;`).

**Cost removed.** A silent `undefined` after a target bump. Locally, the
baseline returns `"lab"` at `--target es2021` and `"undefined"` at
`es2022`; tsc reports `TS2612` at `es2022` but still emits (no
`noEmitOnError`), and transpile-only tools emit without any error. The
`declare` version returns `"lab"` at both targets.

**Verify.**

1. Behavior: the oracle runs both files at `es2021` and `es2022` and
   asserts the values above.
1. Benefit: `tsc --target es2022 --noEmit emit/class/redeclare.ts` prints
   `TS2612`; the `declare-field.ts` build prints no error.

## ES module instead of namespace

**Definition.** A `namespace` with values compiles to an IIFE that assigns
members onto a mutable object; top-level `export` declarations need no
wrapper, and `import * as Geometry` keeps qualified names
([namespaces and modules][namespaces]).

**Use when.**

- A namespace groups values inside an ES module project.
- The file must pass `erasableSyntaxOnly` or run under Node type
  stripping.

**Do not use when.**

- The namespace only contains types: type-only namespaces are erasable and
  Node accepts them ([Node TypeScript][node-ts]).
- Global script (non-module) code relies on declaration merging across
  files.

**Example.**

```typescript
export const unit = 1;
export function area(w: number, h: number): number {
  return w * h * unit;
}
```

Baseline emit (`emit/namespace/ns.ts`, excerpt):

```javascript
export var Geometry;
(function (Geometry) {
    Geometry.unit = 1;
    function area(w, h) {
        return w * h * Geometry.unit;
    }
    Geometry.area = area;
})(Geometry || (Geometry = {}));
```

Runnable: `emit/namespace/module.ts`.

**Cost removed.** The IIFE and the property reads through the namespace
object; the handbook recommends modules for "better tooling support for
bundling". Local: 398 B to 331 B. Runtime: no speedup. For `1e7` calls
Node took 24-85 ms (namespace) vs 62-68 ms (module), and in two of three
runs the namespace build was faster; Bun 6.5-6.8 ms vs 6.6-12 ms. Make
this change for erasability and bundling, not speed.

**Verify.**

1. Behavior: the oracle compares `run(100)` for both files.
1. Benefit: `METRIC module emitted bytes: 398 -> 331`, plus the
   `erasableSyntaxOnly` and Node direct-run checks.

## Native async functions from ES2017

**Definition.** With `--target` below ES2017, `tsc` rewrites each `async`
function into a generator driven by the `__awaiter` helper; at ES2017 and
later it emits `async`/`await` unchanged ([tsconfig target][tsc-target]).

**Use when.**

- `tsc --showConfig` shows `target` below `es2017` while every supported
  runtime implements async functions (Node, Bun, and evergreen browsers
  do).
- A CPU profile of the emitted code shows `__awaiter`, `step`, or
  `fulfilled` frames.

**Do not use when.**

- A supported runtime lacks native async functions: the lowering is the
  compatibility layer.
- Raising `target` also changes class-field semantics you have not
  checked: see [Declare for redeclared fields](#declare-for-redeclared-fields)
  (ES2022 boundary).

**Example.**

```typescript
async function step(i: number): Promise<number> {
  if (i < 0) throw new RangeError("negative");
  return i & 1;
}

export async function run(n: number): Promise<number> {
  let sum = 0;
  for (let i = 0; i < n; i++) sum += await step(i);
  return sum;
}
```

Emitted at `--target es2016` (excerpt):

```javascript
function step(i) {
    return __awaiter(this, void 0, void 0, function* () {
        if (i < 0)
            throw new RangeError("negative");
```

Runnable: `emit/downlevel/async.ts`.

**Cost removed.** The helper, one generator object per call, and its
promise plumbing. Local: 1,479 B to 562 B; `run(1e6)` Node 548-710 ms vs
34-141 ms, Bun 238-970 ms vs 26-36 ms (three shared-machine runs; the
direction held in every run).

**Verify.**

1. Behavior: the oracle compares `run(999)` and the rejection path
   (`fails()` returns the `RangeError` message) at both targets.
1. Benefit: `es2017` output has no `__awaiter(`; `verify.sh measure`
   asserts the candidate median is lower and prints `TIME async`.

## Native private fields from ES2022

**Definition.** Below ES2022, `#field` compiles to a module-level
`WeakMap` plus `__classPrivateFieldGet`/`Set`/`In` helpers; at ES2022+ it
stays a native private field ([classes handbook][classes]).

**Use when.**

- The emitted code shows `new WeakMap()` and `__classPrivateField*`
  helpers, and all supported runtimes implement class fields.

**Do not use when.**

- The same target bump would change field semantics you have not tested
  (define vs assign; see
  [Declare for redeclared fields](#declare-for-redeclared-fields)).

**Example.**

```typescript
export class Counter {
  #count = 0;
  inc(): number {
    return ++this.#count;
  }
  static owns(value: object): boolean {
    return #count in value;
  }
}
```

Emitted at `--target es2021` (excerpt):

```javascript
return __classPrivateFieldSet(this, _Counter_count,
    (_a = __classPrivateFieldGet(this, _Counter_count, "f"), ++_a), "f");
// ...
_Counter_count = new WeakMap();
```

Runnable: `emit/downlevel/private.ts`.

**Cost removed.** Two helper calls and a `WeakMap` lookup per access.
Local: 2,160 B to 497 B; `run(2e7)` Node 428-560 ms vs 20-24 ms, Bun
215-218 ms vs 15 ms (three shared-machine runs).

**Verify.**

1. Behavior: the oracle compares `run(999)`, which includes the `#count in`
   brand check on an instance and on `{}`.
1. Benefit: no `new WeakMap()` in `es2022` output; `verify.sh measure`
   asserts the lower median and prints `TIME private`.

## Native object spread from ES2018

**Definition.** Below ES2018, `{ ...base, ...extra }` compiles to
`Object.assign(Object.assign({}, base), extra)`. `Object.assign` uses
[[Set]], so an own `"__proto__"` key (as `JSON.parse` produces) invokes
the prototype setter, while native spread defines an own property
([MDN spread syntax][mdn-spread]).

**Use when.**

- Output targets ES2017 or lower and spreads objects built from untrusted
  JSON.
- Emitted code shows `Object.assign(Object.assign({}` chains.

**Do not use when.**

- A supported runtime lacks object spread (ES2018).

**Example.**

```typescript
export function merge(base: object, extra: object): object {
  return { ...base, ...extra };
}
const input = JSON.parse('{"__proto__": {"polluted": true}, "id": 1}');
// es2018+: keys ["kind","__proto__","id"], prototype unchanged
// es2017:  keys ["kind","id"], prototype replaced, merged.polluted === true
```

Runnable: `emit/downlevel/spread.ts`.

**Cost removed.** A behavior divergence (prototype replacement) and the
nested `Object.assign` calls. The oracle takes Node's direct execution of
the `.ts` file as the ES semantics and asserts that the `es2018` output
matches it and the `es2017` output does not.

**Verify.**

1. Behavior: `verify.sh emit` compares `es2018` output with the directly
   executed source.
1. Benefit: the `es2017` output contains `Object.assign` and produces the
   different result shown above.

## importHelpers with tslib

**Definition.** `importHelpers` replaces per-file inline helpers
(`__awaiter`, `__decorate`, `__classPrivateFieldGet`, ...) with imports from
`tslib` ([tsconfig importHelpers][tsc-helpers]); `noEmitHelpers` omits them
and assumes globals.

**Use when.**

- `grep -c "var __awaiter" dist/**/*.js` (or another helper) is above 1,
  because every lowered file carries its own copy.
- `tslib` can be a runtime dependency of the package.

**Do not use when.**

- The target is high enough that no helpers are emitted (check first).
- `tslib` is not installed or its version lacks a helper your tsc emits:
  tsc fails with `TS2354` ("This syntax requires an imported helper but
  module 'tslib' cannot be found"), observed locally.

**Example.**

```sh
tsc emit/helpers/a.ts emit/helpers/b.ts emit/helpers/c.ts \
  emit/helpers/main.ts --target es2016 --module esnext \
  --rewriteRelativeImportExtensions --importHelpers --outDir out/tslib
```

Each file then starts with `import { __awaiter } from "tslib";`.
Runnable: `emit/helpers/`.

**Cost removed.** Duplicated helper definitions. Local (four files with
async functions at `es2016`): 4 inline `__awaiter` copies to 0; 4,208 B to
1,624 B total, before bundling. A bundler that deduplicates helpers
shrinks the baseline too; measure the final bundle.

**Verify.**

1. Behavior: the oracle compares `run()` of both builds (needs
   `tslib@2.8.1`, which `verify.sh` installs with `bun add`).
1. Benefit: `METRIC import-helpers inline __awaiter copies: 4 -> 0`.

## Standard decorators and the target

**Definition.** TC39 standard decorators (TypeScript 5.0+, without
`experimentalDecorators`) are lowered to `__esDecorate` and
`__runInitializers` for targets up to ES2025; `--target esnext` emits the
`@decorator` syntax unchanged ([TypeScript 5.0][ts50]).

**Use when.**

- Code with decorators must run on Node: keep the target at or below
  `es2025` (the tsc 7 default).

**Do not use when.**

- Emitting `esnext` for Node 26.8.2: it throws `SyntaxError: Invalid or
  unexpected token` at `@logged` (observed locally). Node's type stripping
  also rejects decorators ([Node TypeScript][node-ts]). Bun 1.4.2 runs
  both the `.ts` source and the `esnext` output.
- The code uses parameter decorators or `emitDecoratorMetadata`: those
  exist only with `experimentalDecorators` ([TypeScript 5.0][ts50]).

**Example.**

```typescript
function logged<This, Args extends unknown[], R>(
  method: (this: This, ...args: Args) => R,
  context: ClassMethodDecoratorContext<This>,
): (this: This, ...args: Args) => R {
  const name = String(context.name);
  return function (this: This, ...args: Args): R {
    calls.push(name);
    return method.apply(this, args);
  };
}
```

Runnable: `emit/decorators/standard.ts`.

**Cost removed.** A startup `SyntaxError` on Node. The lowering adds
helper code at every target up to ES2025.

**Verify.**

1. Behavior: the oracle runs the `es2022` build on Node and checks
   `"6:total"`; with Bun it also runs the source and the `esnext` build.
1. Benefit: the `esnext` build fails on Node with `SyntaxError`, which the
   oracle asserts.

## Decorator metadata retains imports

**Definition.** With `experimentalDecorators` and `emitDecoratorMetadata`,
tsc emits `__metadata("design:paramtypes", [Database])` for decorated
constructors, turning a type-position import into a runtime import that
evaluates the module ([tsconfig emitDecoratorMetadata][tsc-edm]).

**Use when.**

- Startup profiling shows modules loaded only because decorated classes
  name them in constructor parameter types.
- No framework reads `design:*` metadata (DI containers that use
  explicit tokens do not).

**Do not use when.**

- A framework resolves dependencies from `design:paramtypes` (common with
  `reflect-metadata`-based DI): removing the flag breaks injection.

**Example.**

```typescript
import { Database } from "./dep.ts";

function inject(_target: object, _key: string | undefined, _i: number) {}

export class Repository {
  private readonly db: Database;
  constructor(@inject db: Database) {
    this.db = db;
  }
}
```

With the flag, output contains `import { Database } from "./dep.js";` and
`__metadata("design:paramtypes", [Database])`. Runnable:
`emit/decorators/legacy.ts`.

**Cost removed.** One module evaluation (and its transitive imports) per
metadata-retained import. Local: `dep.ts` evaluations 1 to 0.

**Verify.**

1. Behavior: both builds construct and run; the oracle asserts the
   metadata call exists only in the flagged build.
1. Benefit: `METRIC decorator-metadata dep.ts evaluations: 1 -> 0`.

## Top-level import type

**Definition.** `import type { Config } from "./heavy.ts"` is always
erased. Under `verbatimModuleSyntax`, an inline specifier
(`import { type Config }`) is rewritten to `import {} from "./heavy.ts"`,
which still evaluates the module ([TypeScript 5.0][ts50]); Node type
stripping behaves the same way.

**Use when.**

- An import brings in only types from a module with import-time work.
- The project sets `verbatimModuleSyntax` or runs under Node type
  stripping.

**Do not use when.**

- The side effect is required (polyfill, registration): write an explicit
  `import "./module.ts";` so the intent is visible.

**Example.**

```typescript
import type { Config } from "./heavy.ts";

export function run(): number {
  const config: Config = { retries: 1 };
  return config.retries;
}
```

Runnable: `emit/imports/type-only.ts`; baseline `inline-type.ts`; hazard
`value-import.ts` (`import { Config }` without `type`), which Node rejects
with `SyntaxError` because `heavy.ts` has no runtime `Config` export, and
which tsc rejects with `TS1484` under `verbatimModuleSyntax`.

**Cost removed.** One evaluation of `heavy.ts` per process. Local: 1 to 0
in the tsc build and 1 to 0 under Node type stripping. Bun elided the
inline specifier in a manual check (`bun inline-type.ts` printed 0 loads),
so the baseline cost is runtime-dependent.

**Verify.**

1. Behavior: both files return the same `retries` value.
1. Benefit: `METRIC import-type heavy.ts evaluations (tsc): 1 -> 0` and
   `(node): 1 -> 0`.

[enums]: https://www.typescriptlang.org/docs/handbook/enums.html
[node-ts]: https://nodejs.org/api/typescript.html
[tsc-preserve]: https://www.typescriptlang.org/tsconfig/#preserveConstEnums
[ts58]: https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-8.html
[classes]: https://www.typescriptlang.org/docs/handbook/2/classes.html
[tsc-udfcf]: https://www.typescriptlang.org/tsconfig/#useDefineForClassFields
[namespaces]: https://www.typescriptlang.org/docs/handbook/namespaces-and-modules.html
[tsc-target]: https://www.typescriptlang.org/tsconfig/#target
[mdn-spread]: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Spread_syntax
[tsc-helpers]: https://www.typescriptlang.org/tsconfig/#importHelpers
[ts50]: https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-0.html
[tsc-edm]: https://www.typescriptlang.org/tsconfig/#emitDecoratorMetadata
