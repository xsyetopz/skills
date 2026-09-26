// Oracle helpers shared by every construct module. A failed check throws, so
// run.mjs exits nonzero and names the construct. Runs on node and bun.
import { isDeepStrictEqual } from "node:util";

export const runtime = globalThis.Bun
	? `bun ${globalThis.Bun.version}`
	: `node ${process.versions.node}`;

let count = 0;
export const checks = () => count;

export function equal(construct, expected, actual) {
	count++;
	if (!isDeepStrictEqual(expected, actual)) {
		throw new Error(
			`${construct}: expected ${fmt(expected)}, got ${fmt(actual)}`,
		);
	}
}

export function ok(construct, condition, detail) {
	count++;
	if (!condition) throw new Error(`${construct}: ${detail}`);
}

// Both calls must throw the same error class and message, or both return
// deep-equal values.
export function sameOutcome(construct, baseline, candidate) {
	const run = (fn) => {
		try {
			return { value: fn() };
		} catch (error) {
			return { error: `${error?.constructor?.name}: ${error?.message}` };
		}
	};
	equal(construct, run(baseline), run(candidate));
}

// Every array of `length` <= maxLength over `alphabet`: small exhaustive
// input domains catch empty, duplicate, and boundary cases.
export function* arrays(alphabet, maxLength) {
	for (let length = 0; length <= maxLength; length++) {
		for (let code = 0; code < alphabet.length ** length; code++) {
			const out = [];
			let rest = code;
			for (let i = 0; i < length; i++) {
				out.push(alphabet[rest % alphabet.length]);
				rest = Math.floor(rest / alphabet.length);
			}
			yield out;
		}
	}
}

let sink;
export const consume = (value) => {
	sink = value;
};
export const sunk = () => sink;

// Heap bytes allocated by `iterations` calls of fn, V8 only. Needs
// `node --expose-gc`. Returns null elsewhere: JSC's heapStats and
// process.memoryUsage().heapUsed do not count unswept allocations.
// Warm up first so tier-up allocations are excluded; take the minimum of
// several windows so one window with a GC inside it cannot hide the cost.
export function allocatedBytes(fn, iterations = 200, warmup = 5_000) {
	if (globalThis.Bun || typeof globalThis.gc !== "function") return null;
	for (let i = 0; i < warmup; i++) sink = fn(i);
	let best = Infinity;
	for (let window = 0; window < 5; window++) {
		globalThis.gc();
		const before = heapBytes();
		for (let i = 0; i < iterations; i++) sink = fn(i);
		const delta = heapBytes() - before;
		if (delta >= 0) best = Math.min(best, delta);
	}
	return best === Infinity ? null : Math.round(best / iterations);
}

// JS heap plus ArrayBuffer backing stores (typed arrays live outside the
// JS heap, so heapUsed alone would under-count them).
function heapBytes() {
	const { heapUsed, arrayBuffers } = process.memoryUsage();
	return heapUsed + arrayBuffers;
}

// Candidate must allocate at most `ratio` of the baseline per call. Keep
// iterations x bytes/call well below the young generation (a few MiB) so no
// scavenge runs inside a measuring window.
export function allocatesLess(construct, baseline, candidate, options = {}) {
	const { ratio = 0.5, iterations = 200, warmup = 5_000 } = options;
	const before = allocatedBytes(baseline, iterations, warmup);
	const after = allocatedBytes(candidate, iterations, warmup);
	if (before === null || after === null) {
		console.log(`SKIP alloc ${construct}: no V8 heap counter (${runtime})`);
		return;
	}
	console.log(`ALLOC ${construct}: ${before} B/call -> ${after} B/call`);
	ok(construct, after <= before * ratio, `${after} B not <= ${ratio}x`);
}

function fmt(value) {
	try {
		return JSON.stringify(value) ?? String(value);
	} catch {
		return String(value);
	}
}
