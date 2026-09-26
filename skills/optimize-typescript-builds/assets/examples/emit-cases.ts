// Emit and runtime-semantics oracles. Each case compiles a baseline and a
// candidate with tsc, runs both in fresh processes, checks equivalence (or
// the documented divergence), and asserts a deterministic benefit.
import {
  BUN,
  NODE,
  bytes,
  call,
  check,
  emit,
  exists,
  hasBun,
  occurrences,
  read,
  sh,
  tsMajor,
  tsc,
} from "./lib.ts";

function value(name: string, runtime: string, file: string, n?: number) {
  const r = call(runtime, file, n);
  check.ok(name, r.status === 0, `${runtime} ${file} failed:\n${r.out}`);
  return JSON.parse(r.out) as unknown;
}

function erasable(name: string, base: string, cand: string): void {
  const b = tsc([base, "--noEmit", "--erasableSyntaxOnly", "--skipLibCheck"]);
  check.ok(name, b.out.includes("TS1294"), `baseline lacks TS1294:\n${b.out}`);
  const c = tsc([cand, "--noEmit", "--erasableSyntaxOnly", "--skipLibCheck"]);
  check.ok(name, c.status === 0, `candidate not erasable:\n${c.out}`);
  const strip = call(NODE, base, 30);
  check.ok(
    name,
    strip.out.includes("ERR_UNSUPPORTED_TYPESCRIPT_SYNTAX"),
    `node ran the non-erasable baseline:\n${strip.out}`,
  );
}

function enums(): void {
  const dir = "emit/enum";
  const files = ["regular", "const", "as-const"].map((f) => `${dir}/${f}.ts`);
  emit("out/enum", files, ["--target", "es2022"]);
  const expected = value("enum", NODE, "out/enum/regular.js", 3000);
  check.equal("const-enum", expected, value("x", NODE, "out/enum/const.js", 3000));
  check.equal(
    "as-const",
    expected,
    value("as-const", NODE, "out/enum/as-const.js", 3000),
  );
  const regular = read("out/enum/regular.js");
  const inlined = read("out/enum/const.js");
  check.ok("const-enum", regular.includes("(function (Op)"), "no enum IIFE");
  check.ok("const-enum", !inlined.includes("(function (Op)"), "IIFE kept");
  check.ok("const-enum", inlined.includes("0 /* Op.Add */"), "not inlined");
  check.less(
    "const-enum",
    "emitted bytes",
    bytes("out/enum/regular.js"),
    bytes("out/enum/const.js"),
  );
  // Direct execution: the erasable candidate runs under Node type stripping.
  check.equal("as-const", expected, value("as-const", NODE, files[2], 3000));
  erasable("as-const", files[0], files[2]);

  // isolatedModules implies preserveConstEnums; TS 7 also stops inlining.
  emit("out/enum-iso", [files[1]], ["--target", "es2022", "--isolatedModules"]);
  const iso = read("out/enum-iso/const.js");
  check.ok("const-enum-iso", iso.includes("(function (Op)"), "enum erased");
  const cross = [`${dir}/use-levels.ts`, `${dir}/levels.ts`];
  emit("out/levels", cross, ["--target", "es2022"]);
  check.ok(
    "const-enum-cross",
    read("out/levels/use-levels.js").includes("2 /* Level.High */"),
    "cross-file const enum not inlined without isolatedModules",
  );
  emit("out/levels-iso", cross, ["--target", "es2022", "--isolatedModules"]);
  check.equal(
    "const-enum-cross",
    2,
    value("x", NODE, "out/levels-iso/use-levels.js", 20),
  );
  if (tsMajor() >= 7) {
    check.ok("const-enum-iso", iso.includes("Op.Add"), "TS 7 inlined");
    check.ok(
      "const-enum-cross",
      read("out/levels-iso/use-levels.js").includes("Level.High"),
      "TS 7 inlined a cross-file const enum under isolatedModules",
    );
  } else {
    check.skip("const-enum-iso", `TS 7 inlining check; tsc ${tsMajor()}`);
  }
}

function classes(): void {
  const base = "emit/class/param-props.ts";
  const cand = "emit/class/fields.ts";
  emit("out/class", [base, cand], ["--target", "es2022"]);
  const expected = value("param-props", NODE, "out/class/param-props.js", 50);
  check.equal("fields", expected, value("x", NODE, "out/class/fields.js", 50));
  check.equal("fields", expected, value("x", NODE, cand, 50));
  const js = read("out/class/param-props.js");
  check.ok("param-props", js.includes("this.x = x;"), "no assignment");
  erasable("fields", base, cand);

  // Define semantics: a redeclared field resets the inherited value.
  const re = ["emit/class/redeclare.ts", "emit/class/declare-field.ts"];
  emit("out/field21", re, ["--target", "es2021"]);
  // tsc reports TS2612 under define semantics but still emits (no
  // noEmitOnError); single-file transpilers emit the same code silently.
  const define = tsc([
    ...re,
    "--outDir",
    "out/field22",
    "--module",
    "esnext",
    "--rewriteRelativeImportExtensions",
    "--skipLibCheck",
    "--target",
    "es2022",
  ]);
  check.ok("redeclare", define.out.includes("TS2612"), `no TS2612:\n${define.out}`);
  check.ok(
    "redeclare",
    !define.out.includes("declare-field.ts("),
    `declare-field.ts reported errors:\n${define.out}`,
  );
  check.equal("redeclare", "lab", value("x", NODE, "out/field21/redeclare.js"));
  check.equal(
    "redeclare",
    "undefined",
    value("x", NODE, "out/field22/redeclare.js"),
  );
  for (const out of ["out/field21", "out/field22"]) {
    check.equal("declare", "lab", value("x", NODE, `${out}/declare-field.js`));
  }
}

function namespaces(): void {
  const base = "emit/namespace/ns.ts";
  const cand = "emit/namespace/module.ts";
  emit("out/ns", [base, cand], ["--target", "es2022"]);
  const expected = value("namespace", NODE, "out/ns/ns.js", 100);
  check.equal("module", expected, value("x", NODE, "out/ns/module.js", 100));
  check.ok("namespace", read("out/ns/ns.js").includes("(function ("), "IIFE");
  check.less(
    "module",
    "emitted bytes",
    bytes("out/ns/ns.js"),
    bytes("out/ns/module.js"),
  );
  erasable("module", base, cand);
}

function targets(): void {
  const pairs: [string, string, string, string][] = [
    ["async", "es2016", "es2017", "__awaiter("],
    ["private", "es2021", "es2022", "new WeakMap()"],
  ];
  for (const [name, low, high, helper] of pairs) {
    const src = `emit/downlevel/${name}.ts`;
    emit(`out/${low}`, [src], ["--target", low]);
    emit(`out/${high}`, [src], ["--target", high]);
    const lowJs = `out/${low}/${name}.js`;
    const highJs = `out/${high}/${name}.js`;
    check.equal(name, value(name, NODE, lowJs, 999), value(name, NODE, highJs, 999));
    check.ok(name, read(lowJs).includes(helper), `${low} lacks ${helper}`);
    check.ok(name, !read(highJs).includes(helper), `${high} has ${helper}`);
    check.less(name, "emitted bytes", bytes(lowJs), bytes(highJs));
  }
  const asyncFails = (dir: string) =>
    sh(NODE, [
      "--input-type=module",
      "-e",
      `const m = await import("./${dir}/async.js");` +
        "console.log(await m.fails());",
    ]).out.trim();
  check.equal("async-reject", asyncFails("out/es2016"), asyncFails("out/es2017"));

  // Object spread lowered to Object.assign triggers the __proto__ setter.
  const src = "emit/downlevel/spread.ts";
  emit("out/es2017", [src], ["--target", "es2017"]);
  emit("out/es2018", [src], ["--target", "es2018"]);
  const native = value("spread", NODE, src);
  check.equal("spread", native, value("spread", NODE, "out/es2018/spread.js"));
  const lowered = value("spread", NODE, "out/es2017/spread.js");
  check.ok(
    "spread-es2017",
    JSON.stringify(lowered) !== JSON.stringify(native),
    "Object.assign lowering unexpectedly matched native spread",
  );
  check.ok(
    "spread-es2017",
    read("out/es2017/spread.js").includes("Object.assign"),
    "no Object.assign in es2017 output",
  );
}

function helpers(): void {
  const files = ["a", "b", "c", "main"].map((f) => `emit/helpers/${f}.ts`);
  emit("out/inline", files, ["--target", "es2016"]);
  if (!exists("node_modules/tslib/package.json")) {
    check.skip("import-helpers", "tslib not installed in the work copy");
    return;
  }
  emit("out/tslib", files, ["--target", "es2016", "--importHelpers"]);
  check.equal(
    "import-helpers",
    value("x", NODE, "out/inline/main.js"),
    value("x", NODE, "out/tslib/main.js"),
  );
  let inlineCount = 0;
  let tslibCount = 0;
  let inlineBytes = 0;
  let tslibBytes = 0;
  for (const f of ["a", "b", "c", "main"]) {
    inlineCount += occurrences(read(`out/inline/${f}.js`), "var __awaiter");
    tslibCount += occurrences(read(`out/tslib/${f}.js`), "var __awaiter");
    inlineBytes += bytes(`out/inline/${f}.js`);
    tslibBytes += bytes(`out/tslib/${f}.js`);
  }
  check.less("import-helpers", "inline __awaiter copies", inlineCount, tslibCount);
  check.less("import-helpers", "emitted bytes", inlineBytes, tslibBytes);
}

function decorators(): void {
  const std = "emit/decorators/standard.ts";
  emit("out/dec22", [std], ["--target", "es2022"]);
  emit("out/decnext", [std], ["--target", "esnext"]);
  const lowered = read("out/dec22/standard.js");
  check.ok("decorators", lowered.includes("__esDecorate"), "not lowered");
  check.equal("decorators", "6:total", value("x", NODE, "out/dec22/standard.js"));
  const native = call(NODE, "out/decnext/standard.js");
  check.ok(
    "decorators-esnext",
    native.status !== 0 && native.out.includes("SyntaxError"),
    `node parsed native decorators:\n${native.out}`,
  );
  const stripped = call(NODE, std);
  check.ok(
    "decorators-strip",
    stripped.status !== 0,
    "node type stripping ran decorator syntax",
  );
  if (hasBun()) {
    check.equal("decorators-bun", "6:total", value("x", BUN, std));
    check.equal(
      "decorators-bun",
      "6:total",
      value("x", BUN, "out/decnext/standard.js"),
    );
  } else {
    check.skip("decorators-bun", "bun not found");
  }

  const legacy = ["emit/decorators/legacy.ts", "emit/decorators/dep.ts"];
  const flags = ["--target", "es2022", "--experimentalDecorators"];
  emit("out/meta", legacy, [...flags, "--emitDecoratorMetadata"]);
  emit("out/nometa", legacy, flags);
  check.ok(
    "decorator-metadata",
    read("out/meta/legacy.js").includes('__metadata("design:paramtypes"'),
    "no design:paramtypes metadata",
  );
  check.less(
    "decorator-metadata",
    "dep.ts evaluations",
    Number(value("x", NODE, "out/meta/legacy.js")),
    Number(value("x", NODE, "out/nometa/legacy.js")),
  );
}

function imports(): void {
  const dir = "emit/imports";
  const files = ["heavy", "inline-type", "type-only"].map(
    (f) => `${dir}/${f}.ts`,
  );
  emit("out/imports", files, ["--target", "es2022", "--verbatimModuleSyntax"]);
  check.ok(
    "import-type",
    read("out/imports/inline-type.js").includes('import {} from "./heavy.js"'),
    "inline type specifier did not leave a side-effect import",
  );
  const inline = Number(value("x", NODE, "out/imports/inline-type.js"));
  const typeOnly = Number(value("x", NODE, "out/imports/type-only.js"));
  check.equal("import-type", 10, typeOnly);
  check.less("import-type", "heavy.ts evaluations (tsc)", inline % 10, typeOnly % 10);
  // Node type stripping follows the same rule without any tsconfig.
  const inlineTs = Number(value("x", NODE, `${dir}/inline-type.ts`));
  const typeTs = Number(value("x", NODE, `${dir}/type-only.ts`));
  check.less("import-type", "heavy.ts evaluations (node)", inlineTs % 10, typeTs % 10);
  const bare = call(NODE, `${dir}/value-import.ts`);
  check.ok(
    "value-import",
    bare.status !== 0 && bare.out.includes("SyntaxError"),
    `node ran a type imported as a value:\n${bare.out}`,
  );
  const vms = tsc([
    `${dir}/value-import.ts`,
    "--noEmit",
    "--verbatimModuleSyntax",
    "--allowImportingTsExtensions",
    "--skipLibCheck",
  ]);
  check.ok("value-import", vms.out.includes("TS1484"), `no TS1484:\n${vms.out}`);
}

function runtimes(): void {
  const bad = "runtime/type-error.ts";
  const r = tsc([bad, "--noEmit", "--skipLibCheck"]);
  check.ok("strip-no-check", r.out.includes("TS2322"), "tsc missed TS2322");
  check.equal("strip-no-check", 8, value("x", NODE, bad));
  if (!hasBun()) {
    check.skip("bun", "bun not found");
    return;
  }
  check.equal("bun-no-check", 8, value("x", BUN, bad));
  check.equal(
    "bun-enum",
    value("x", NODE, "out/enum/regular.js", 3000),
    value("x", BUN, "emit/enum/regular.ts", 3000),
  );
  const entry = "emit/enum/use-levels.ts";
  const bundled = sh(BUN, ["build", entry, "--target", "node"]);
  const single = sh(BUN, ["build", entry, "--no-bundle"]);
  check.ok("bun-bundle", bundled.status === 0, bundled.out);
  check.ok(
    "bun-bundle",
    !bundled.out.includes("Level.High") && bundled.out.includes("2 /*"),
    `bundle did not inline the const enum:\n${bundled.out}`,
  );
  check.ok(
    "bun-no-bundle",
    single.out.includes("Level.High"),
    `transpile-only output inlined the const enum:\n${single.out}`,
  );
}

export function runEmit(): void {
  enums();
  classes();
  namespaces();
  targets();
  helpers();
  decorators();
  imports();
  runtimes();
}
