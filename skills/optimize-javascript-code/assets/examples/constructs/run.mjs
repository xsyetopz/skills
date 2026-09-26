// Entry point for verify.sh. Portable across node and bun.
//   node --expose-gc run.mjs verify   oracles + benefit assertions
//   node run.mjs benchmark            harness smoke: every pair runs once
//   node run.mjs measure [filter]     timed pairs; each side of each pair
//                                     runs in its own child process so
//                                     type feedback from one side cannot
//                                     slow down or speed up the other
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import * as allocation from "./allocation.mjs";
import * as async from "./async.mjs";
import { measure, report } from "./bench.mjs";
import { checks, runtime } from "./check.mjs";
import * as shapes from "./shapes.mjs";

const modules = { shapes, allocation, async };
const pairs = Object.values(modules).flatMap((m) => m.benches);
const [mode = "verify", arg = "", side = ""] = process.argv.slice(2);
const TIMED = { warmupMs: 300, sampleMs: 50, samples: 20 };

if (mode === "verify") {
	console.log(`runtime: ${runtime} (${process.platform} ${process.arch})`);
	for (const [name, module] of Object.entries(modules)) {
		await module.verify();
		console.log(`PASS ${name}`);
	}
	console.log(`PASS ${checks()} checks`);
} else if (mode === "benchmark") {
	console.log(`runtime: ${runtime} (${process.platform} ${process.arch})`);
	const smoke = { warmupMs: 1, sampleMs: 1, samples: 1 };
	for (const [name, baseline, candidate] of pairs) {
		report(`${name} baseline`, measure(baseline, smoke));
		report(`${name} candidate`, measure(candidate, smoke));
	}
	console.log("SMOKE PASSED: every pair ran; not a timing result.");
} else if (mode === "measure") {
	console.log(`runtime: ${runtime} (${process.platform} ${process.arch})`);
	for (const [name] of pairs) {
		if (!name.includes(arg)) continue;
		for (const which of ["baseline", "candidate"]) {
			const child = spawnSync(
				process.execPath,
				[fileURLToPath(import.meta.url), "measure-one", name, which],
				{ stdio: "inherit" },
			);
			if (child.status !== 0) process.exit(child.status ?? 1);
		}
	}
} else if (mode === "measure-one") {
	const pair = pairs.find(([name]) => name === arg);
	const fn = side === "baseline" ? pair[1] : pair[2];
	report(`${arg} ${side}`, measure(fn, TIMED));
} else {
	console.error("usage: run.mjs verify|benchmark|measure [filter]");
	process.exit(2);
}
