// Type-checker and build oracles. Fixtures are generated into the work copy.
// Every comparison runs --singleThreaded so Types, Instantiations, Symbols,
// and Memory used repeat run to run; timings are printed, never asserted.
import {
  bytes,
  check,
  diag,
  exists,
  read,
  tsMajor,
  tsc,
  write,
} from "./lib.ts";

const STRICT = ["--singleThreaded", "--extendedDiagnostics"];

function measure(name: string, args: string[], cwd?: string) {
  const r = tsc([...args, ...STRICT], cwd);
  const errors = r.out.split("\n").filter((l) => l.includes("error TS"));
  const d = diag(r.out);
  const time = d["Check time"];
  console.log(
    `DIAG ${name}: Types=${d["Types"]} Instantiations=${d["Instantiations"]}` +
      ` Memory=${d["Memory used"]}K Check=${time}s Files=${d["Files"]}`,
  );
  return { d, errors, out: r.out, status: r.status };
}

function noErrors(name: string, m: { errors: string[] }): void {
  check.ok(name, m.errors.length === 0, m.errors.slice(0, 3).join("\n"));
}

// Wiki: large unions are compared member by member; a base type is one check.
// Returns [union source, base-type source] with n members and calls uses.
function unionSources(n: number, calls: number): [string, string] {
  const u: string[] = [];
  const b: string[] = ["export interface EvBase { at: number }"];
  for (let i = 0; i < n; i++) {
    u.push(`export interface Ev${i} { at: number; p${i}: string }`);
    b.push(`export interface Ev${i} extends EvBase { p${i}: string }`);
  }
  const all = Array.from({ length: n }, (_, i) => `Ev${i}`).join(" | ");
  u.push(`export type Ev = ${all};`, "declare function handle(e: Ev): void;");
  b.push("declare function handle(e: EvBase): void;");
  for (let j = 0; j < calls; j++) {
    const decl =
      `declare const v${j}: { at: number; p${(j * 13) % n}: string;` +
      ` q${j}: boolean };\nhandle(v${j});`;
    u.push(decl);
    b.push(decl);
  }
  // Array literals of distinct object types force union subtype reduction.
  for (let j = 0; j < calls; j++) {
    const items = `[v${j}, v${(j + 1) % calls}, v${(j + 2) % calls}]`;
    u.push(`export const arr${j} = ${items} as Ev[];`);
    b.push(`export const arr${j} = ${items} as EvBase[];`);
  }
  return [u.join("\n") + "\n", b.join("\n") + "\n"];
}

function unions(): void {
  const [u, b] = unionSources(300, 600);
  write("gen/union.ts", u);
  write("gen/base-type.ts", b);
  const flags = ["--noEmit", "--skipLibCheck"];
  const base = measure("union", ["gen/union.ts", ...flags]);
  const cand = measure("base-type", ["gen/base-type.ts", ...flags]);
  noErrors("union", base);
  noErrors("base-type", cand);
  check.less("base-type", "Memory used K", base.d["Memory used"], cand.d["Memory used"]);
  check.less("base-type", "Types", base.d["Types"], cand.d["Types"]);
}

function intersections(): void {
  const n = 60;
  const m = 400;
  const inter: string[] = [];
  const iface: string[] = [];
  for (let i = 0; i < n; i++) {
    inter.push(`type B${i} = { k${i}: number; s${i}: string };`);
    iface.push(`interface B${i} { k${i}: number; s${i}: string }`);
  }
  for (let j = 0; j < m; j++) {
    const mem = Array.from({ length: 12 }, (_, t) => `B${(j * 7 + t) % n}`);
    const sub = mem.slice(0, 6);
    inter.push(`type T${j} = ${mem.join(" & ")} & { own${j}: string };`);
    inter.push(`type S${j} = ${sub.join(" & ")};`);
    iface.push(`interface T${j} extends ${mem.join(", ")} { own${j}: string }`);
    iface.push(`interface S${j} extends ${sub.join(", ")} {}`);
    const fn = `export function f${j}(x: T${j}): S${j} { return x; }`;
    inter.push(fn);
    iface.push(fn);
  }
  write("gen/intersections.ts", inter.join("\n") + "\n");
  write("gen/interfaces.ts", iface.join("\n") + "\n");
  const flags = ["--noEmit", "--skipLibCheck"];
  const base = measure("intersections", ["gen/intersections.ts", ...flags]);
  const cand = measure("interfaces", ["gen/interfaces.ts", ...flags]);
  noErrors("intersections", base);
  noErrors("interfaces", cand);
  check.less("interfaces", "Types", base.d["Types"], cand.d["Types"]);
}

function recursion(): void {
  const flags = ["--noEmit", "--skipLibCheck"];
  const base = measure("non-tail", ["checker/non-tail.ts", ...flags]);
  check.ok(
    "tail-recursion",
    base.out.includes("TS2589"),
    "non-tail recursion did not hit TS2589",
  );
  noErrors("tail-recursion", measure("tail", ["checker/tail.ts", ...flags]));
}

function conditionals(): void {
  const lines = (named: boolean) => {
    const out = ["interface Box<T> { v: T }"];
    const cond =
      "U extends string ? { s: U } : U extends number ? { n: U } : Box<U>";
    if (named) {
      out.push(`type Wrap<U> = ${cond};`);
      out.push("function f<U>(x: U): Wrap<U> { return x as any; }");
    } else {
      out.push(`function f<U>(x: U): ${cond} { return x as any; }`);
    }
    for (let j = 0; j < 2000; j++) {
      const arg = [`"a${j % 50}"`, String(j % 50), "true"][j % 3];
      out.push(`export const r${j} = f(${arg});`);
    }
    return out.join("\n") + "\n";
  };
  write("gen/cond-inline.ts", lines(false));
  write("gen/cond-named.ts", lines(true));
  const flags = ["--noEmit", "--skipLibCheck"];
  const a = measure("cond-inline", ["gen/cond-inline.ts", ...flags]);
  const b = measure("cond-named", ["gen/cond-named.ts", ...flags]);
  noErrors("cond-inline", a);
  noErrors("cond-named", b);
  console.log(
    "REPORT named-conditional: no benefit asserted; Instantiations " +
      `${a.d["Instantiations"]} -> ${b.d["Instantiations"]}`,
  );
}

function returnTypes(): void {
  const inf: string[] = [
    "function base(n: number) { return { id: n, name: String(n)," +
      " tags: [String(n)], meta: { created: n, updated: n," +
      " owner: { id: n, name: String(n) } } }; }",
  ];
  const ann: string[] = [
    "export interface Owner { id: number; name: string }",
    "export interface Meta { created: number; updated: number; owner: Owner }",
    "export interface Rec { id: number; name: string; tags: string[];" +
      " meta: Meta }",
    "function base(n: number): Rec { return { id: n, name: String(n)," +
      " tags: [String(n)], meta: { created: n, updated: n," +
      " owner: { id: n, name: String(n) } } }; }",
  ];
  const probe: string[] = [
    'import type * as I from "./inferred.ts";',
    'import type * as A from "./annotated.ts";',
    "type Eq<X, Y> = [X] extends [Y] ? ([Y] extends [X] ? true : false)" +
      " : false;",
  ];
  for (let j = 0; j < 200; j++) {
    inf.push(
      `export function get${j}(n: number) { return { ...base(n), k${j}: n }; }`,
    );
    ann.push(`export interface Rec${j} extends Rec { k${j}: number }`);
    ann.push(
      `export function get${j}(n: number): Rec${j}` +
        ` { return { ...base(n), k${j}: n }; }`,
    );
    probe.push(
      `export const eq${j}: Eq<ReturnType<typeof I.get${j}>,` +
        ` ReturnType<typeof A.get${j}>> = true;`,
    );
  }
  write("gen/ret/inferred.ts", inf.join("\n") + "\n");
  write("gen/ret/annotated.ts", ann.join("\n") + "\n");
  write("gen/ret/probe.ts", probe.join("\n") + "\n");
  const flags = ["--declaration", "--emitDeclarationOnly", "--skipLibCheck"];
  const a = measure("inferred", ["gen/ret/inferred.ts", ...flags, "--outDir", "out/ret-inf"]);
  const b = measure("annotated", ["gen/ret/annotated.ts", ...flags, "--outDir", "out/ret-ann"]);
  noErrors("inferred", a);
  noErrors("annotated", b);
  const eq = tsc([
    "gen/ret/probe.ts",
    "--noEmit",
    "--skipLibCheck",
    "--allowImportingTsExtensions",
  ]);
  check.ok("return-types", eq.status === 0, `return types differ:\n${eq.out}`);
  check.less(
    "return-types",
    ".d.ts bytes",
    bytes("out/ret-inf/inferred.d.ts"),
    bytes("out/ret-ann/annotated.d.ts"),
  );
  check.less("return-types", "Types", a.d["Types"], b.d["Types"]);
}

function libCheck(): void {
  write("gen/lib/app.ts", "export const total: number = [1, 2].length;\n");
  const base = measure("lib-checked", ["gen/lib/app.ts", "--noEmit"]);
  const cand = measure("skip-lib", ["gen/lib/app.ts", "--noEmit", "--skipLibCheck"]);
  noErrors("lib-checked", base);
  noErrors("skip-lib", cand);
  check.less("skip-lib-check", "Types", base.d["Types"], cand.d["Types"]);
}

function typesArray(): void {
  const decls = Array.from(
    { length: 3000 },
    (_, i) => `declare function big${i}(x: { v${i}: number }): string;`,
  );
  write("gen/types/node_modules/@types/big/index.d.ts", decls.join("\n") + "\n");
  write("gen/types/node_modules/@types/big/package.json", '{"name":"@types/big"}\n');
  write("gen/types/src/app.ts", "export const n: number = 1;\n");
  const cfg = (types: string) =>
    `{"compilerOptions":{"noEmit":true,"skipLibCheck":true${types}},` +
    '"include":["src"]}\n';
  write("gen/types/tsconfig.all.json", cfg(',"types":["*"]'));
  write("gen/types/tsconfig.none.json", cfg(',"types":[]'));
  const base = measure("types-all", ["-p", "gen/types/tsconfig.all.json"]);
  const cand = measure("types-none", ["-p", "gen/types/tsconfig.none.json"]);
  noErrors("types-all", base);
  noErrors("types-none", cand);
  check.less("types-array", "Files", base.d["Files"], cand.d["Files"]);
  check.less("types-array", "Symbols", base.d["Symbols"], cand.d["Symbols"]);
}

function include(): void {
  write("gen/inc/src/app.ts", "export const app = 1;\n");
  for (let i = 0; i < 50; i++) {
    write(`gen/inc/fixtures/case${i}.ts`, `export const c${i} = ${i};\n`);
  }
  const cfg = (inc: string) =>
    `{"compilerOptions":{"noEmit":true,"skipLibCheck":true},${inc}}\n`;
  write("gen/inc/tsconfig.wide.json", cfg('"include":["."]'));
  write("gen/inc/tsconfig.src.json", cfg('"include":["src"]'));
  const count = (p: string) =>
    tsc(["-p", p, "--listFilesOnly"]).out.trim().split("\n").length;
  check.less(
    "include",
    "listed files",
    count("gen/inc/tsconfig.wide.json"),
    count("gen/inc/tsconfig.src.json"),
  );
}

function incremental(): void {
  write("gen/incr/app.ts", read("gen/union.ts"));
  write(
    "gen/incr/tsconfig.json",
    '{"compilerOptions":{"noEmit":true,"skipLibCheck":true,' +
      '"incremental":true,"tsBuildInfoFile":"cache/app.tsbuildinfo"},' +
      '"include":["app.ts"]}\n',
  );
  const cold = measure("incremental-cold", ["-p", "gen/incr"]);
  const warm = measure("incremental-warm", ["-p", "gen/incr"]);
  check.ok(
    "incremental",
    exists("gen/incr/cache/app.tsbuildinfo"),
    "no .tsbuildinfo written",
  );
  check.less("incremental", "Check time s", cold.d["Check time"], warm.d["Check time"]);
}

function references(): void {
  write(
    "gen/refs/core/tsconfig.json",
    '{"compilerOptions":{"composite":true,"outDir":"dist","rootDir":".",' +
      '"skipLibCheck":true},"include":["index.ts"]}\n',
  );
  write("gen/refs/core/index.ts", "export const core = (n: number) => n + 1;\n");
  write(
    "gen/refs/app/tsconfig.json",
    '{"compilerOptions":{"composite":true,"outDir":"dist","rootDir":".",' +
      '"skipLibCheck":true},"include":["main.ts"],' +
      '"references":[{"path":"../core"}]}\n',
  );
  write(
    "gen/refs/app/main.ts",
    'import { core } from "../core/index.js";\nexport const v = core(1);\n',
  );
  const first = tsc(["-b", "gen/refs/app", "--verbose"]);
  check.ok("project-references", first.status === 0, first.out);
  check.ok(
    "project-references",
    exists("gen/refs/core/dist/index.d.ts"),
    "referenced project emitted no declarations",
  );
  const second = tsc(["-b", "gen/refs/app", "--verbose"]);
  const upToDate = second.out.split("\n").filter((l) => /up to date/i.test(l));
  console.log(`METRIC project-references up-to-date projects: ${upToDate.length}`);
  check.ok("project-references", upToDate.length >= 2, second.out);
  if (tsMajor() >= 7) {
    const par = tsc(["-b", "gen/refs/app", "--force", "--builders", "2"]);
    check.ok("builders", par.status === 0, par.out);
  }
}

function declarations(): void {
  write(
    "gen/decl/annotated.ts",
    "export interface Made { n: number; label: string }\n" +
      "export function make(n: number): Made {\n" +
      "  return { n: n, label: String(n) };\n}\n",
  );
  write(
    "gen/decl/inferred.ts",
    "function compute(n: number) { return { n: n, label: String(n) }; }\n" +
      "export function make(n: number) {\n  return compute(n);\n}\n",
  );
  const flags = ["--declaration", "--emitDeclarationOnly", "--skipLibCheck"];
  const iso = tsc(["gen/decl/inferred.ts", ...flags, "--isolatedDeclarations", "--outDir", "out/decl-x"]);
  check.ok("isolated-declarations", /TS90\d\d/.test(iso.out), iso.out);
  const big = "gen/ret/annotated.ts";
  const full = measure("decl-checked", [big, ...flags, "--outDir", "out/decl-full"]);
  const fast = measure("decl-nocheck", [
    big,
    ...flags,
    "--isolatedDeclarations",
    "--noCheck",
    "--outDir",
    "out/decl-fast",
  ]);
  noErrors("decl-checked", full);
  noErrors("decl-nocheck", fast);
  check.equal(
    "isolated-declarations",
    read("out/decl-full/annotated.d.ts"),
    read("out/decl-fast/annotated.d.ts"),
  );
  check.less("isolated-declarations", "Types", full.d["Types"], fast.d["Types"]);

  // --noCheck emit: same JavaScript without the checker's work.
  const js = ["gen/union.ts", "--skipLibCheck", "--target", "es2022"];
  const checked = measure("emit-checked", [...js, "--outDir", "out/js-full"]);
  const unchecked = measure("emit-nocheck", [...js, "--noCheck", "--outDir", "out/js-fast"]);
  noErrors("emit-checked", checked);
  check.equal(
    "no-check-emit",
    read("out/js-full/union.js"),
    read("out/js-fast/union.js"),
  );
  check.less("no-check-emit", "Types", checked.d["Types"], unchecked.d["Types"]);
}

function nativeCompiler(): void {
  if (tsMajor() < 7) {
    check.skip("typescript-7", `tsc major ${tsMajor()} is below 7`);
    return;
  }
  write("gen/ts7/app.ts", "export const n = 1;\n");
  const removed: [string[], string][] = [
    [["--target", "es5"], "TS5108"],
    [["--downlevelIteration"], "TS5102"],
    [["--baseUrl", "."], "TS5102"],
    [["--moduleResolution", "node10"], "TS5108"],
  ];
  for (const [opts, code] of removed) {
    const r = tsc(["gen/ts7/app.ts", "--noEmit", ...opts]);
    check.ok("removed-options", r.out.includes(code), `${opts}: ${r.out}`);
  }
  const files: string[] = [];
  for (let f = 0; f < 8; f++) {
    write(`gen/par/m${f}.ts`, unionSources(120, 240)[0]);
    files.push(`gen/par/m${f}.ts`);
  }
  const run = (extra: string[]) => {
    const r = tsc([
      ...files,
      "--noEmit",
      "--skipLibCheck",
      "--extendedDiagnostics",
      ...extra,
    ]);
    const d = diag(r.out);
    const errs = r.out.split("\n").filter((l) => l.includes("error TS"));
    console.log(
      `DIAG checkers ${extra.join(" ")}: Types=${d["Types"]}` +
        ` Memory=${d["Memory used"]}K Check=${d["Check time"]}s`,
    );
    return { d, errs };
  };
  const one = run(["--checkers", "1"]);
  const four = run(["--checkers", "4"]);
  check.equal("checkers", one.errs, four.errs);
  check.ok(
    "checkers",
    four.d["Memory used"] > one.d["Memory used"],
    "4 checkers did not use more memory than 1",
  );
  // 6.0 defaults adopted by 7: types [] and rootDir "./" (tsconfig dir).
  write(
    "gen/types/tsconfig.default.json",
    '{"compilerOptions":{"noEmit":true,"skipLibCheck":true},' +
      '"include":["src"]}\n',
  );
  const dflt = diag(
    tsc(["-p", "gen/types/tsconfig.default.json", "--extendedDiagnostics", "--singleThreaded"]).out,
  );
  const none = diag(
    tsc(["-p", "gen/types/tsconfig.none.json", "--extendedDiagnostics", "--singleThreaded"]).out,
  );
  check.equal("default-types", none["Files"], dflt["Files"]);
  check.equal("default-types", none["Symbols"], dflt["Symbols"]);
  write("gen/root/src/a.ts", "export const a = 1;\n");
  write(
    "gen/root/tsconfig.json",
    '{"compilerOptions":{"outDir":"dist","skipLibCheck":true},' +
      '"include":["src"]}\n',
  );
  // tsc 7 reports TS5011 when sources sit below the tsconfig directory and
  // rootDir is unset, and still emits to dist/src/.
  const root = tsc(["-p", "gen/root"]);
  check.ok("default-rootdir", root.out.includes("TS5011"), root.out);
  check.ok("default-rootdir", exists("gen/root/dist/src/a.js"), "no dist/src");
  const fixed = tsc(["-p", "gen/root", "--rootDir", "gen/root/src", "--outDir", "gen/root/dist2"]);
  check.ok("default-rootdir", fixed.status === 0, fixed.out);
  check.ok("default-rootdir", exists("gen/root/dist2/a.js"), "rootDir not applied");
  const pprof = tsc(["gen/ts7/app.ts", "--noEmit", "--pprofDir", "out/pprof"]);
  check.ok("pprof", pprof.out.includes("CPU profile:"), pprof.out);
  const trace = tsc([
    "gen/ts7/app.ts",
    "--noEmit",
    "--generateTrace",
    "out/trace",
  ]);
  check.ok("trace", exists("out/trace/trace.json"), trace.out);
  check.ok("trace", exists("out/trace/legend.json"), "no legend.json");
}

export function runChecker(): void {
  unions();
  intersections();
  recursion();
  conditionals();
  returnTypes();
  libCheck();
  typesArray();
  include();
  incremental();
  references();
  declarations();
  nativeCompiler();
}
