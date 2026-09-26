// Entry point: node harness.ts emit|checker|measure (run from the work copy).
import { check, tsc, TSC } from "./lib.ts";
import { runEmit } from "./emit-cases.ts";
import { runChecker } from "./checker-cases.ts";
import { runMeasure } from "./measure.ts";

const mode = process.argv[2] ?? "verify";
console.log(`tsc: ${TSC} (${tsc(["--version"]).out.trim()})`);
console.log(`node: ${process.version}`);
if (mode === "emit" || mode === "verify" || mode === "measure") runEmit();
if (mode === "checker" || mode === "verify" || mode === "measure") runChecker();
if (mode === "measure") runMeasure();
console.log(`PASS ${check.passed} checks, ${check.skipped} skipped (${mode})`);
