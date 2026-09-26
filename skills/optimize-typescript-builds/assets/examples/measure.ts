// Timing mode. Prints machine-specific medians; asserts only the direction
// for the two lowering cases whose gap is an order of magnitude locally.
import { BUN, NODE, check, diag, hasBun, sh, tsMajor, tsc } from "./lib.ts";

function median(runtime: string, file: string, n: number): number {
  const r = sh(runtime, ["time.ts", file, String(n), "7"]);
  if (r.status !== 0) throw new Error(`${runtime} ${file}: ${r.out}`);
  return (JSON.parse(r.out.trim()) as { median: number }).median;
}

function pair(name: string, base: string, cand: string, n: number, gate: boolean) {
  const runtimes = hasBun() ? [NODE, BUN] : [NODE];
  for (const rt of runtimes) {
    const b = median(rt, base, n);
    const c = median(rt, cand, n);
    const label = rt === NODE ? "node" : "bun";
    console.log(`TIME ${name} ${label}: ${b} ms -> ${c} ms (n=${n})`);
    if (gate) check.ok(name, c < b, `${label}: candidate not faster`);
  }
}

function startup(): void {
  const spawn = (file: string) => {
    const samples: number[] = [];
    for (let i = 0; i < 11; i++) {
      const start = performance.now();
      const r = sh(NODE, ["call.ts", file, "10"]);
      samples.push(performance.now() - start);
      if (r.status !== 0) throw new Error(r.out);
    }
    samples.sort((a, b) => a - b);
    return Number(samples[5].toFixed(1));
  };
  const ts = spawn("emit/class/fields.ts");
  const js = spawn("out/class/fields.js");
  console.log(`TIME node startup: fields.ts ${ts} ms, fields.js ${js} ms`);
}

function checkTimes(): void {
  const t = (args: string[]) =>
    diag(tsc([...args, "--noEmit", "--skipLibCheck", "--extendedDiagnostics"]).out)[
      "Check time"
    ];
  for (const f of ["gen/union.ts", "gen/base-type.ts"]) {
    const s = [1, 2, 3].map(() => t([f, "--singleThreaded"])).sort((a, b) => a - b);
    console.log(`TIME check ${f}: ${s[1]} s (median of 3)`);
  }
  if (tsMajor() < 7) return;
  const files = Array.from({ length: 8 }, (_, i) => `gen/par/m${i}.ts`);
  for (const c of ["1", "2", "4", "8"]) {
    const s = [1, 2, 3].map(() => t([...files, "--checkers", c])).sort((a, b) => a - b);
    console.log(`TIME check --checkers ${c}: ${s[1]} s (median of 3)`);
  }
}

export function runMeasure(): void {
  pair("async", "out/es2016/async.js", "out/es2017/async.js", 1_000_000, true);
  pair("private", "out/es2021/private.js", "out/es2022/private.js", 20_000_000, true);
  pair("const-enum", "out/enum/regular.js", "out/enum/const.js", 100_000_000, false);
  pair("as-const", "out/enum/regular.js", "out/enum/as-const.js", 100_000_000, false);
  pair("fields", "out/class/param-props.js", "out/class/fields.js", 10_000_000, false);
  pair("module", "out/ns/ns.js", "out/ns/module.js", 10_000_000, false);
  startup();
  checkTimes();
}
