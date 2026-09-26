// Minimal timing harness for node and bun: warmup, fixed-duration samples,
// a result sink, and per-sample ns/op. Use the project's harness (mitata,
// tinybench, ...) when one exists; this file shows the required parts.
import { consume } from "./check.mjs";

const now = () => process.hrtime.bigint(); // monotonic ns (bigint)

// Calls fn until `ms` elapsed; returns [iterations, elapsed ns].
function runFor(fn, ms) {
	const budget = BigInt(Math.round(ms * 1e6));
	const start = now();
	let iterations = 0;
	let elapsed = 0n;
	do {
		for (let i = 0; i < 64; i++) consume(fn(iterations + i));
		iterations += 64;
		elapsed = now() - start;
	} while (elapsed < budget);
	return [iterations, elapsed];
}

export function measure(fn, { warmupMs = 200, sampleMs = 50, samples = 15 }) {
	runFor(fn, warmupMs); // let the JIT tier up before recording
	const nsPerOp = [];
	for (let s = 0; s < samples; s++) {
		const [iterations, elapsed] = runFor(fn, sampleMs);
		nsPerOp.push(Number(elapsed) / iterations);
	}
	nsPerOp.sort((a, b) => a - b);
	const pick = (q) =>
		nsPerOp[Math.min(nsPerOp.length - 1, Math.floor(q * nsPerOp.length))];
	return { median: pick(0.5), min: nsPerOp[0], p90: pick(0.9), samples };
}

export function report(name, result) {
	const f = (v) => v.toFixed(1).padStart(10);
	console.log(
		`${name.padEnd(44)} median ${f(result.median)} ns/op` +
			` min ${f(result.min)} p90 ${f(result.p90)} n=${result.samples}`,
	);
}
