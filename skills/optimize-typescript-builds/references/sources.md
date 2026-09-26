# Sources

Primary documentation behind the cards. Behavior marked "observed
locally" in a card was measured with tsc 7.0.2, Node 26.8.2, and Bun 1.4.2
on macOS arm64; re-run the oracle on your versions before relying on it.

## Compiler

| Topic | Source |
| --- | --- |
| TypeScript 7 native compiler, removed options, defaults, `--checkers`, `--builders`, `tsc6` | [Announcing TypeScript 7.0](https://devblogs.microsoft.com/typescript/announcing-typescript-7-0/) |
| Native port background | [A 10x Faster TypeScript](https://devblogs.microsoft.com/typescript/typescript-native-port/) |
| Native compiler source | [microsoft/typescript-go](https://github.com/microsoft/typescript-go) |
| Checker performance guidance, tracing, `extendedDiagnostics` | [Performance wiki](https://github.com/microsoft/TypeScript/wiki/Performance) |
| Compiler options | [TSConfig reference](https://www.typescriptlang.org/tsconfig/) |
| Standard decorators, `verbatimModuleSyntax` | [TypeScript 5.0](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-0.html) |
| Tail-recursive conditional types | [TypeScript 4.5](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-4-5.html) |
| `isolatedDeclarations` | [TypeScript 5.5](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-5.html) |
| `--noCheck`, `--stopOnBuildErrors` | [TypeScript 5.6](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-6.html) |
| `erasableSyntaxOnly` | [TypeScript 5.8](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-8.html) |
| Project references, `tsc -b` | [Project references](https://www.typescriptlang.org/docs/handbook/project-references.html) |
| Enums and const enum pitfalls | [Enums](https://www.typescriptlang.org/docs/handbook/enums.html) |
| Parameter properties, private fields, `declare` fields | [Classes](https://www.typescriptlang.org/docs/handbook/2/classes.html) |
| Namespaces versus modules | [Namespaces and modules](https://www.typescriptlang.org/docs/handbook/namespaces-and-modules.html) |
| Trace analysis | [@typescript/analyze-trace](https://www.npmjs.com/package/@typescript/analyze-trace) |

## Runtimes

| Topic | Source |
| --- | --- |
| Node type stripping, versions, unsupported syntax | [Node.js TypeScript](https://nodejs.org/api/typescript.html) |
| Bun TypeScript configuration | [Bun TypeScript](https://bun.com/docs/runtime/typescript) |
| Bun bundler, no type-checking, no down-conversion | [Bun bundler](https://bun.com/docs/bundler) |
| Bun legacy decorator fix | [Bun v1.3.11](https://bun.com/blog/bun-v1.3.11) |
| `Object.assign` versus spread | [MDN spread syntax](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Spread_syntax) |
| Go profile viewer | [pprof](https://github.com/google/pprof) |
