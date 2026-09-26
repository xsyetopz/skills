// Imports a module and prints JSON of `await run(...args)`. Runs under
// `node call.ts FILE [N]` (type stripping) and `bun call.ts FILE [N]`.
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";

const [file, arg] = process.argv.slice(2);
if (file === undefined) throw new Error("usage: call.ts FILE [N]");
const mod = (await import(pathToFileURL(resolve(file)).href)) as {
  run: (...args: number[]) => unknown;
};
const result = await mod.run(...(arg === undefined ? [] : [Number(arg)]));
console.log(JSON.stringify(result));
