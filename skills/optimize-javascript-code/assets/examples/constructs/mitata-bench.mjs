// The same pairs through mitata (the harness bun's docs recommend for
// microbenchmarks). Needs `bun add mitata@1.0.34` in a scratch copy; run
// with node or bun. Usage: mitata-bench.mjs [filter]
import { bench, do_not_optimize, run, summary } from "mitata";
import * as allocation from "./allocation.mjs";
import * as shapes from "./shapes.mjs";

const filter = process.argv[2] ?? "";
for (const module of [shapes, allocation]) {
	for (const [name, baseline, candidate] of module.benches) {
		if (!name.includes(filter)) continue;
		summary(() => {
			let i = 0;
			bench(`${name} baseline`, () => do_not_optimize(baseline(i++)));
			bench(`${name} candidate`, () => do_not_optimize(candidate(i++)));
		});
	}
}
await run({ colors: false });
