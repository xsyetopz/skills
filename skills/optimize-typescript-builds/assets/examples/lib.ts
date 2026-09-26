// Shared oracle helpers. Erasable TypeScript only: runs under Node type
// stripping (Node 22.18+) and Bun without a build step.
import { spawnSync } from "node:child_process";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";

export const WORK = process.cwd();
export const TSC = process.env["TSC"] ?? "tsc";
export const BUN = process.env["BUN"] ?? "bun";
export const NODE = process.execPath;

export interface Run {
  status: number;
  out: string;
}

export function sh(cmd: string, args: string[], cwd: string = WORK): Run {
  const r = spawnSync(cmd, args, { cwd, encoding: "utf8" });
  if (r.error) return { status: 127, out: String(r.error) };
  return { status: r.status ?? 1, out: `${r.stdout}${r.stderr}` };
}

export function tsc(args: string[], cwd: string = WORK): Run {
  return sh(TSC, args, cwd);
}

let major = -1;
export function tsMajor(): number {
  if (major < 0) {
    const m = /Version (\d+)\./.exec(tsc(["--version"]).out);
    major = m ? Number(m[1]) : 0;
  }
  return major;
}

export function hasBun(): boolean {
  return sh(BUN, ["--version"]).status === 0;
}

// Parses `--extendedDiagnostics` lines such as "Types:  3094",
// "Memory used:  52473K", and "Check time:  0.458s" into numbers.
export function diag(out: string): Record<string, number> {
  const result: Record<string, number> = {};
  for (const line of out.split("\n")) {
    const m = /^([A-Za-z/ ]+):\s+([\d.]+)([Ks]?)\s*$/.exec(line.trim());
    if (m) result[m[1].trim()] = Number(m[2]);
  }
  return result;
}

export function read(path: string): string {
  return readFileSync(join(WORK, path), "utf8");
}

export function write(path: string, text: string): void {
  const full = join(WORK, path);
  mkdirSync(dirname(full), { recursive: true });
  writeFileSync(full, text);
}

export function exists(path: string): boolean {
  return existsSync(join(WORK, path));
}

export function bytes(path: string): number {
  return Buffer.byteLength(read(path));
}

export function occurrences(text: string, needle: string): number {
  return text.split(needle).length - 1;
}

// Runs `run()` of a module in a fresh process so module-evaluation
// counters and globals never leak between cases.
export function call(runtime: string, file: string, arg?: number): Run {
  const args = ["call.ts", file];
  if (arg !== undefined) args.push(String(arg));
  const r = sh(runtime, args);
  return { status: r.status, out: r.out.trim() };
}

export const check = {
  passed: 0,
  skipped: 0,
  equal(name: string, expected: unknown, actual: unknown): void {
    const e = JSON.stringify(expected);
    const a = JSON.stringify(actual);
    if (e !== a) throw new Error(`${name}: expected ${e}, got ${a}`);
    check.passed++;
  },
  ok(name: string, condition: boolean, detail: string): void {
    if (!condition) throw new Error(`${name}: ${detail}`);
    check.passed++;
  },
  less(name: string, metric: string, base: number, cand: number): void {
    console.log(`METRIC ${name} ${metric}: ${base} -> ${cand}`);
    check.ok(name, cand < base, `${metric} ${cand} is not below ${base}`);
  },
  skip(name: string, reason: string): void {
    console.log(`SKIP ${name}: ${reason}`);
    check.skipped++;
  },
};

// Compiles files with explicit options and no tsconfig, as ES modules.
export function emit(out: string, files: string[], opts: string[]): Run {
  const args = [
    ...files,
    "--outDir",
    out,
    "--module",
    "esnext",
    "--rewriteRelativeImportExtensions",
    "--skipLibCheck",
    ...opts,
  ];
  const r = tsc(args);
  if (r.status !== 0) throw new Error(`tsc ${args.join(" ")}\n${r.out}`);
  return r;
}
