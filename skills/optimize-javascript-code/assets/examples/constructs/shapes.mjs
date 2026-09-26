// Object shapes, elements kinds, and keyed collections. Portable oracles;
// engine-internal evidence lives in v8-probes.mjs and jsc-probes.mjs.
import { allocatesLess, arrays, equal, ok } from "./check.mjs";

// --- Initialize every field in the constructor ---------------------------
export function baselineRecords(values) {
	return values.map((value, index) => {
		const record = {};
		if (index % 2 === 0) {
			record.x = value;
			record.y = index;
		} else {
			record.y = index; // different insertion order: different shape
			record.x = value;
		}
		return record;
	});
}

export class Point {
	constructor(x, y) {
		this.x = x; // same fields, same order, every time
		this.y = y;
	}
}

export function candidateRecords(values) {
	return values.map((value, index) => new Point(value, index));
}

export function sumRecords(records) {
	let sum = 0;
	for (const record of records) sum += record.x + record.y;
	return sum;
}

// --- Assign undefined instead of delete ---------------------------------
export function baselineClear(session) {
	delete session.token;
	return session;
}

export function candidateClear(session) {
	session.token = undefined; // property stays; shape stays
	return session;
}

// --- Monomorphic call site ---------------------------------------------
export const mixedShapes = (n) =>
	Array.from({ length: n }, (_, i) => {
		switch (i % 5) {
			case 0:
				return { x: i, y: 1 };
			case 1:
				return { y: 1, x: i };
			case 2:
				return { x: i, y: 1, z: 0 };
			case 3:
				return { x: i, y: 1, w: 0 };
			default:
				return { z: 0, x: i, y: 1 };
		}
	});

export function lengthSquared(p) {
	return p.x * p.x + p.y * p.y; // one property-load site per field
}

export function baselineTotal(points) {
	let total = 0;
	for (const p of points) total += lengthSquared(p);
	return total;
}

export function candidateTotal(points) {
	// Normalize once at the boundary; the hot loop sees one shape.
	const uniform = points.map((p) => new Point(p.x, p.y));
	let total = 0;
	for (const p of uniform) total += lengthSquared(p);
	return total;
}

// --- Packed arrays -------------------------------------------------------
export function baselineSquares(n) {
	const out = new Array(n); // HOLEY_SMI_ELEMENTS from the start
	for (let i = 0; i < n; i++) out[i] = i * i;
	return out;
}

export function candidateSquares(n) {
	const out = []; // PACKED_SMI_ELEMENTS; push keeps it packed
	for (let i = 0; i < n; i++) out.push(i * i);
	return out;
}

// --- One elements kind per array ---------------------------------------
// Parsed readings where some are missing.
export function baselineReadings(raw) {
	return raw.map((s) => (s === "" ? null : Number(s))); // mixed kinds
}

export function candidateReadings(raw) {
	const values = new Float64Array(raw.length);
	const present = new Uint8Array(raw.length);
	for (let i = 0; i < raw.length; i++) {
		if (raw[i] !== "") {
			values[i] = Number(raw[i]);
			present[i] = 1;
		}
	}
	return { values, present };
}

export const readingsAsArray = ({ values, present }) =>
	Array.from(values, (v, i) => (present[i] ? v : null));

// --- Typed arrays for numeric records -----------------------------------
export function baselineParticles(n) {
	const list = [];
	for (let i = 0; i < n; i++) list.push({ x: i * 0.5, v: i * 1.5 });
	for (const p of list) p.x += p.v;
	return list;
}

export function candidateParticles(n) {
	const x = new Float64Array(n);
	const v = new Float64Array(n);
	for (let i = 0; i < n; i++) {
		x[i] = i * 0.5;
		v[i] = i * 1.5;
	}
	for (let i = 0; i < n; i++) x[i] += v[i];
	return { x, v };
}

// --- Map for dynamic keys -----------------------------------------------
export function baselineCounts(words) {
	const counts = {};
	for (const w of words) counts[w] = (counts[w] || 0) + 1;
	return counts;
}

export function candidateCounts(words) {
	const counts = new Map();
	for (const w of words) counts.set(w, (counts.get(w) ?? 0) + 1);
	return counts;
}

// --- Set membership instead of Array.prototype.includes -----------------
export const baselineKnown = (allowed, queries) =>
	queries.filter((q) => allowed.includes(q));

export function candidateKnown(allowed, queries) {
	const set = new Set(allowed); // built once per call, O(n)
	return queries.filter((q) => set.has(q));
}

const time = (fn) => {
	const start = performance.now();
	fn();
	return performance.now() - start;
};

export function verify() {
	for (const values of arrays([-1, 0, 2.5], 4)) {
		equal(
			"constructor-init",
			sumRecords(baselineRecords(values)),
			sumRecords(candidateRecords(values)),
		);
		equal(
			"monomorphic",
			baselineTotal(mixedShapes(values.length)),
			candidateTotal(mixedShapes(values.length)),
		);
		const raw = values.map((v) => (v === 0 ? "" : String(v)));
		equal(
			"elements-kind",
			baselineReadings(raw),
			readingsAsArray(candidateReadings(raw)),
		);
	}
	// delete vs undefined: equal for readers of the value, different for
	// `in`, Object.keys, and JSON.stringify. Check which one callers use.
	const a = baselineClear({ id: 1, token: "t" });
	const b = candidateClear({ id: 1, token: "t" });
	equal("avoid-delete value", a.token, b.token);
	equal("avoid-delete json", JSON.stringify(a), JSON.stringify(b));
	equal(
		"avoid-delete in (differs)",
		["token" in a, "token" in b],
		[false, true],
	);
	for (const n of [0, 1, 7]) {
		equal("packed-array", baselineSquares(n), candidateSquares(n));
	}
	// Holes are skipped by map/forEach; a packed array has no holes.
	equal("holes skipped by map", new Array(3).map(() => 1).length, 3);
	equal("holes not own", 0 in new Array(3).map(() => 1), false);
	// fill(obj) packs the array but every slot is the same object.
	const shared = new Array(2).fill({ value: 0 });
	shared[0].value = 1;
	equal("fill shares one object (hazard)", shared[1].value, 1);
	const rows = Array.from({ length: 2 }, () => ({ value: 0 }));
	rows[0].value = 1;
	equal("Array.from makes independent rows", rows[1].value, 0);
	const p = baselineParticles(5);
	const q = candidateParticles(5);
	equal(
		"typed-array",
		p.map((e) => e.x),
		Array.from(q.x),
	);
	// Float64Array coerces: this is the semantic cost of the representation.
	equal("typed-array coercion", Array.from(new Float64Array(["1", {}])), [
		1,
		NaN,
	]);
	allocatesLess(
		"typed-array",
		() => baselineParticles(2_000),
		() => candidateParticles(2_000),
		{ iterations: 10, warmup: 200 },
	);
	const words = ["b", "a", "b", "10", "2", "__proto__", "constructor"];
	const counts = candidateCounts(words);
	equal(
		"map counts",
		[...counts],
		[
			["b", 2],
			["a", 1],
			["10", 1],
			["2", 1],
			["__proto__", 1],
			["constructor", 1],
		],
	);
	const broken = baselineCounts(words);
	equal(
		"object counts break on inherited keys",
		typeof broken.constructor,
		"string",
	);
	equal(
		"object key order (differs)",
		Object.keys(baselineCounts(["b", "2", "10"])),
		["2", "10", "b"],
	);
	for (const allowed of arrays(["a", "b", NaN], 3)) {
		const queries = ["a", "c", NaN];
		equal(
			"set-membership",
			baselineKnown(allowed, queries),
			candidateKnown(allowed, queries),
		);
	}
	// indexOf uses ===; includes and Set use SameValueZero.
	equal("sameValueZero", [[NaN].indexOf(NaN), [NaN].includes(NaN)], [-1, true]);
	const allowed = Array.from({ length: 20_000 }, (_, i) => `k${i}`);
	const queries = Array.from({ length: 2_000 }, (_, i) => `k${i * 13}`);
	equal(
		"set-membership large",
		baselineKnown(allowed, queries),
		candidateKnown(allowed, queries),
	);
	const slow = time(() => baselineKnown(allowed, queries));
	const fast = time(() => candidateKnown(allowed, queries));
	console.log(
		`TIME set-membership: ${slow.toFixed(2)} ms -> ` +
			`${fast.toFixed(2)} ms (2,000 queries x 20,000 keys)`,
	);
	ok("set-membership", fast * 3 < slow, "Set not 3x faster at this size");
}

export function sumAll(values) {
	let sum = 0;
	for (let i = 0; i < values.length; i++) sum += values[i];
	return sum;
}

const WORDS = Array.from({ length: 256 }, (_, i) => `w${i % 97}`);
const MIXED = mixedShapes(256);
const UNIFORM = MIXED.map((p) => new Point(p.x, p.y)); // shaped at source
const HOLEY = baselineSquares(4_096);
const PACKED = candidateSquares(4_096);
export const benches = [
	[
		"constructor-init",
		(i) => sumRecords(baselineRecords([i, 1, 2, 3])),
		(i) => sumRecords(candidateRecords([i, 1, 2, 3])),
	],
	[
		"monomorphic (5 shapes -> 1)",
		() => baselineTotal(MIXED),
		() => baselineTotal(UNIFORM),
	],
	[
		"monomorphic (normalize per call)",
		() => baselineTotal(MIXED),
		() => candidateTotal(MIXED),
	],
	[
		"packed-array build",
		() => baselineSquares(256),
		() => candidateSquares(256),
	],
	["packed-array read", () => sumAll(HOLEY), () => sumAll(PACKED)],
	["typed-array", () => baselineParticles(256), () => candidateParticles(256)],
	["map-counts", () => baselineCounts(WORDS), () => candidateCounts(WORDS)],
];
