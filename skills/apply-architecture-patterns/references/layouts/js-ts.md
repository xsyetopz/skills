# JavaScript and TypeScript

The module is the privacy boundary.
A binding is not exported unless another module imports it.
For a class member that must be private at runtime, use `#name`.
Use ES modules, and one `export` on each declaration instead of a list at the end.

## Order in a file

1. Imports: packages, then relative paths, with type-only names marked `type`.
1. Module constants.
1. Types and interfaces (TypeScript).
1. The main exported class or functions, with each class's members together.
1. Unexported classes and helpers, after the code that uses them.

Inside a class: `static` members, `#` fields, constructor, public methods, `#` methods.
Tests go beside the code as `<name>.test.ts`,
or in the test directory the runner is configured for.

## TypeScript

With `erasableSyntaxOnly` (TypeScript 5.8 and later),
write only syntax that erases to plain JavaScript.

- No `enum`: use a `const` object with `as const` and a union type.
- No `namespace` or `module` blocks: use a file as the module.
- No constructor parameter properties: declare the field, then assign it in the constructor.
- Relative imports name the real extension (`./dependency.ts`).
  Set `rewriteRelativeImportExtensions` if the build emits `.js`.
- `private` is erased and gives no runtime privacy, so prefer `#name` when privacy matters.

```ts
import { type Dependency, dependency } from "./dependency.ts";

export const PUBLIC_CONSTANT = 1;
const PRIVATE_CONSTANT = 2;

export const Mode = { Fast: "fast", Safe: "safe" } as const;
export type Mode = (typeof Mode)[keyof typeof Mode];

export class PublicType {
  #state: number;
  readonly dependency: Dependency;

  constructor(dep: Dependency) {
    this.#state = PRIVATE_CONSTANT;
    this.dependency = dep;
  }

  publicMethod(): void {
    this.#privateMethod();
  }

  #privateMethod(): void {
    privateHelper(this.#state);
  }
}

function privateHelper(state: number): number {
  return dependency(state);
}

export function publicFunction(): void {}
```

## JavaScript

The same order, without types.
Set `"type": "module"` in `package.json` and write the file extension in relative imports.

```js
import { dependency } from "./dependency.js";

export const PUBLIC_CONSTANT = 1;
const PRIVATE_CONSTANT = 2;

export class PublicType {
  #state = PRIVATE_CONSTANT;

  publicMethod() {
    this.#privateMethod();
  }

  #privateMethod() {
    privateHelper(this.#state);
  }
}

function privateHelper(state) {
  return dependency(state);
}

export function publicFunction() {}
```
