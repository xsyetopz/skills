// Allocation, iteration, strings, regular expressions, cloning, and
// exceptions. Each pair is observably equivalent on the documented domain;
// verify() proves it and asserts the measured benefit where one exists.
import { allocatesLess, arrays, equal, ok } from "./check.mjs";

// --- Fuse map/filter/reduce chains --------------------------------------
export const baselineEvenSquares = (values) =>
	values
		.filter((v) => v % 2 === 0)
		.map((v) => v * v)
		.reduce((sum, v) => sum + v, 0);

export function candidateEvenSquares(values) {
	let sum = 0;
	for (let i = 0; i < values.length; i++) {
		const v = values[i];
		if (v % 2 === 0) sum += v * v;
	}
	return sum;
}

// --- Hoist closures out of hot calls ------------------------------------
function countIf(values, predicate) {
	let count = 0;
	for (let i = 0; i < values.length; i++) if (predicate(values[i])) count++;
	return count;
}

export const baselineAbove = (values, t) => countIf(values, (v) => v > t);

export function candidateAbove(values, t) {
	let count = 0;
	for (let i = 0; i < values.length; i++) if (values[i] > t) count++;
	return count;
}

// --- for loop vs forEach (semantics differ on holes) --------------------
export function forEachSum(values) {
	let sum = 0;
	values.forEach((v) => {
		sum += v;
	});
	return sum;
}

export function forLoopSum(values) {
	let sum = 0;
	for (let i = 0; i < values.length; i++) sum += values[i];
	return sum;
}

// --- Append with push, not concat ---------------------------------------
export function baselineCollect(values) {
	let out = [];
	for (const v of values) out = out.concat([v]); // copies out every time
	return out;
}

export function candidateCollect(values) {
	const out = [];
	for (const v of values) out.push(v);
	return out;
}

// --- String building: += (ropes) vs array join ---------------------------
export function joinCsv(words) {
	const parts = [];
	for (const w of words) parts.push(w);
	return parts.join(",");
}

export function concatCsv(words) {
	let out = "";
	for (let i = 0; i < words.length; i++) {
		if (i > 0) out += ",";
		out += words[i];
	}
	return out;
}

// --- Hoist regular-expression literals -----------------------------------
export const baselineIsId = (s) => /^[a-z][a-z0-9_]{0,31}$/.test(s);

const ID = /^[a-z][a-z0-9_]{0,31}$/; // no g/y flag: no lastIndex state
export const candidateIsId = (s) => ID.test(s);

// --- Cache RegExp objects built from runtime strings ----------------------
const escape_ = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

export const baselineHasWord = (text, word) =>
	new RegExp(`\\b${escape_(word)}\\b`, "u").test(text);

const wordCache = new Map(); // bounded: keys come from a fixed vocabulary
export function candidateHasWord(text, word) {
	let re = wordCache.get(word);
	if (re === undefined) {
		re = new RegExp(`\\b${escape_(word)}\\b`, "u");
		wordCache.set(word, re);
	}
	return re.test(text);
}

// --- Sticky regex tokenizer ----------------------------------------------
const TOKEN_AT_START = /^\s*(\w+|[^\s\w])/;
export function sliceTokens(text) {
	const out = [];
	let pos = 0;
	while (pos < text.length) {
		const m = TOKEN_AT_START.exec(text.slice(pos));
		if (m === null) break;
		out.push(m[1]);
		pos += m[0].length;
	}
	return out;
}

const TOKEN = /\s*(\w+|[^\s\w])/y;
export function stickyTokens(text) {
	const out = [];
	TOKEN.lastIndex = 0;
	while (TOKEN.lastIndex < text.length) {
		const m = TOKEN.exec(text); // matches only at lastIndex
		if (m === null) break;
		out.push(m[1]);
	}
	return out;
}

// --- Copy the changed path instead of deep cloning -----------------------
export function baselineBump(state, index) {
	const next = JSON.parse(JSON.stringify(state));
	next.items[index].qty += 1;
	return next;
}

export function candidateBump(state, index) {
	const items = state.items.slice();
	items[index] = { ...items[index], qty: items[index].qty + 1 };
	return { ...state, items }; // untouched subtrees are shared
}

// --- structuredClone instead of a JSON round trip (correctness) ----------
export const jsonCopy = (value) => JSON.parse(JSON.stringify(value));
export const structuredCopy = (value) => structuredClone(value);

// --- try/catch stays in optimized code -----------------------------------
export function parseAllOrNull(lines) {
	const out = [];
	for (const line of lines) {
		try {
			out.push(JSON.parse(line)); // per-item recovery
		} catch {
			out.push(null);
		}
	}
	return out;
}

export function parseAllOrThrow(lines) {
	try {
		return lines.map((line) => JSON.parse(line)); // one bad line aborts all
	} catch {
		return null;
	}
}

const STATE = {
	user: { name: "a", prefs: { theme: "dark", langs: ["en", "pl"] } },
	items: Array.from({ length: 50 }, (_, id) => ({ id, qty: id })),
};
const DATA = Array.from({ length: 64 }, (_, i) => i);
const WORDS = Array.from({ length: 200 }, (_, i) => `w${i}`);
const TEXT = "let x = 10 + foo * 3 ; ".repeat(20);

export function verify() {
	for (const values of arrays([-2, 0, 1, 3], 4)) {
		equal(
			"fuse-chain",
			baselineEvenSquares(values),
			candidateEvenSquares(values),
		);
		equal("hoist-closure", baselineAbove(values, 0), candidateAbove(values, 0));
		equal("for-loop", forEachSum(values), forLoopSum(values));
		equal("push-not-concat", baselineCollect(values), candidateCollect(values));
		const words = values.map(String);
		equal("string-concat", joinCsv(words), concatCsv(words));
	}
	// forEach skips holes; an indexed loop reads them as undefined.
	// biome-ignore lint/suspicious/noSparseArray: the hole is what this check is about
	const holey = [1, , 3];
	equal(
		"for-loop holes (differs)",
		[forEachSum(holey), forLoopSum(holey)],
		[4, NaN],
	);
	// concat([v]) wraps v, so array elements stay nested exactly as push.
	equal(
		"push-not-concat nested",
		baselineCollect([[1], [2]]),
		candidateCollect([[1], [2]]),
	);
	allocatesLess(
		"fuse-chain",
		() => baselineEvenSquares(DATA),
		() => candidateEvenSquares(DATA),
		{ ratio: 0.1 },
	);
	allocatesLess(
		"hoist-closure",
		(i) => baselineAbove(DATA, i & 31),
		(i) => candidateAbove(DATA, i & 31),
		{ ratio: 0.1 },
	);
	allocatesLess(
		"push-not-concat",
		() => baselineCollect(DATA),
		() => candidateCollect(DATA),
		{ ratio: 0.5 },
	);
	// Rope evidence is engine-internal: see v8-probes.mjs / jsc-probes.mjs.
	// Allocation deltas for this pair were unstable across tiers on node
	// 26.8.2, so no allocation assertion is made here; use measure mode.

	for (const s of [
		"",
		"a",
		"a_1",
		"1a",
		"A",
		"a".repeat(32),
		"a".repeat(33),
		"a\n",
	]) {
		equal("hoist-regex", baselineIsId(s), candidateIsId(s));
	}
	// A shared /g or /y regex keeps lastIndex between calls.
	const G = /a/g;
	equal(
		"shared global regex (hazard)",
		[G.test("a"), G.test("a")],
		[true, false],
	);
	allocatesLess(
		"hoist-regex",
		(i) => baselineIsId(i & 1 ? "ab" : "a1"),
		(i) => candidateIsId(i & 1 ? "ab" : "a1"),
		{ ratio: 0.5 },
	);
	for (const w of ["foo", "a.b", "x+", "é"]) {
		for (const t of ["foo bar", "a.b c", "axb", "x+ y", "é"]) {
			equal("regex-cache", baselineHasWord(t, w), candidateHasWord(t, w));
		}
	}
	allocatesLess(
		"regex-cache",
		() => baselineHasWord("the foo bar", "foo"),
		() => candidateHasWord("the foo bar", "foo"),
		{ ratio: 0.5 },
	);

	for (const t of ["", " ", "a", "a+b", "  let x=1;", "é!", TEXT]) {
		equal("sticky-regex", sliceTokens(t), stickyTokens(t));
	}

	for (const index of [0, 49]) {
		equal(
			"copy-changed-path",
			baselineBump(STATE, index),
			candidateBump(STATE, index),
		);
	}
	const bumped = candidateBump(STATE, 3);
	ok(
		"copy-changed-path",
		bumped.user === STATE.user,
		"untouched subtree should be shared",
	);
	ok("copy-changed-path", STATE.items[3].qty === 3, "input mutated");
	allocatesLess(
		"copy-changed-path",
		(i) => baselineBump(STATE, i % 50),
		(i) => candidateBump(STATE, i % 50),
		{ ratio: 0.5, iterations: 50 },
	);

	const odd = {
		missing: undefined,
		nan: NaN,
		when: new Date(0),
		tags: new Set(["a"]),
	};
	const viaJson = jsonCopy(odd);
	const viaClone = structuredCopy(odd);
	equal("structured-clone keeps types", viaClone, odd);
	equal(
		"json loses types",
		[
			Object.hasOwn(viaJson, "missing"),
			viaJson.nan,
			typeof viaJson.when,
			viaJson.tags,
		],
		[false, null, "string", {}],
	);
	let cloneError = "none";
	try {
		structuredClone({ f() {} });
	} catch (error) {
		cloneError = error.name;
	}
	equal("structured-clone throws on functions", cloneError, "DataCloneError");

	const lines = ['{"a":1}', "oops", "2"];
	equal("try-catch per item", parseAllOrNull(lines), [{ a: 1 }, null, 2]);
	equal("try-catch hoisted (differs)", parseAllOrThrow(lines), null);
}

export const benches = [
	[
		"fuse-chain",
		() => baselineEvenSquares(DATA),
		() => candidateEvenSquares(DATA),
	],
	[
		"hoist-closure",
		(i) => baselineAbove(DATA, i & 31),
		(i) => candidateAbove(DATA, i & 31),
	],
	["for-loop (forEach -> for)", () => forEachSum(DATA), () => forLoopSum(DATA)],
	[
		"push-not-concat",
		() => baselineCollect(DATA),
		() => candidateCollect(DATA),
	],
	["string (join -> +=)", () => joinCsv(WORDS), () => concatCsv(WORDS)],
	[
		"hoist-regex",
		(i) => baselineIsId(i & 1 ? "ab" : "a1"),
		(i) => candidateIsId(i & 1 ? "ab" : "a1"),
	],
	[
		"regex-cache",
		() => baselineHasWord("the foo bar", "foo"),
		() => candidateHasWord("the foo bar", "foo"),
	],
	["sticky-regex", () => sliceTokens(TEXT), () => stickyTokens(TEXT)],
	[
		"copy-changed-path",
		(i) => baselineBump(STATE, i % 50),
		(i) => candidateBump(STATE, i % 50),
	],
	[
		"clone (JSON -> structuredClone)",
		() => jsonCopy(STATE),
		() => structuredCopy(STATE),
	],
];
