// Prints the median wall time in ms of `await run(N)` over REPS runs after
// one warmup call. Usage: node time.ts FILE N [REPS]  (or bun time.ts ...)
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";

const [file, rawN, rawReps] = process.argv.slice(2);
if (file === undefined || rawN === undefined) {
  throw new Error("usage: time.ts FILE N [REPS]");
}
const mod = (await import(pathToFileURL(resolve(file)).href)) as {
  run: (n: number) => unknown;
};
const n = Number(rawN);
const reps = Number(rawReps ?? 5);
let sink = JSON.stringify(await mod.run(Math.min(n, 1000)));
const samples: number[] = [];
for (let i = 0; i < reps; i++) {
  const start = performance.now();
  sink = JSON.stringify(await mod.run(n));
  samples.push(performance.now() - start);
}
samples.sort((a, b) => a - b);
const median = samples[Math.floor(samples.length / 2)];
console.log(JSON.stringify({ median: Number(median.toFixed(2)), sink }));
