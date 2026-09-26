// Promises, microtasks, event-loop responsiveness, workers, and streams.
// Every oracle awaits all work it starts, so no test passes by returning
// before the candidate finishes.

import { monitorEventLoopDelay } from "node:perf_hooks";
import { Readable, Writable } from "node:stream";
import { pipeline } from "node:stream/promises";
import { MessageChannel, Worker } from "node:worker_threads";
import { equal, ok } from "./check.mjs";

const sleep = (ms, value) =>
	new Promise((resolve) => setTimeout(resolve, ms, value));

// --- Promise.all for independent awaits ---------------------------------
export async function baselineFetchAll(ids, load) {
	const out = [];
	for (const id of ids) out.push(await load(id)); // one at a time
	return out;
}

export const candidateFetchAll = (ids, load) =>
	Promise.all(ids.map((id) => load(id))); // all in flight, order kept

// --- Await async callbacks (forEach does not) ---------------------------
export async function brokenSaveAll(items, save) {
	items.forEach(async (item) => {
		await save(item); // forEach ignores the returned promise
	});
}

export async function fixedSaveAll(items, save) {
	for (const item of items) await save(item);
}

// --- Bounded concurrency -------------------------------------------------
export async function mapLimit(items, limit, fn) {
	const results = new Array(items.length);
	let next = 0;
	async function lane() {
		while (next < items.length) {
			const index = next++;
			results[index] = await fn(items[index], index);
		}
	}
	const lanes = Math.min(limit, items.length);
	await Promise.all(Array.from({ length: lanes }, lane));
	return results;
}

// --- Drop redundant async wrappers ---------------------------------------
export const getValue = () => Promise.resolve(42);
export async function wrappedValue() {
	return getValue(); // resolving with a promise adds thenable-job ticks
}
export const chainedValue = () =>
	getValue()
		.then((v) => v)
		.then((v) => v);

// --- return await inside try ---------------------------------------------
const failing = () => Promise.reject(new Error("boom"));
export async function returnWithoutAwait() {
	try {
		return failing(); // rejection escapes the catch below
	} catch {
		return "handled";
	}
}
export async function returnAwait() {
	try {
		return await failing(); // rejection is caught here
	} catch {
		return "handled";
	}
}

// Microtask turns until fn() settles, counted by a parallel await loop.
export async function ticksToSettle(fn) {
	let turns = 0;
	let settled = false;
	const done = fn().then(
		() => (settled = true),
		() => (settled = true),
	);
	while (!settled && turns < 100) {
		await null;
		turns++;
	}
	await done;
	return turns;
}

// --- Coalesce notifications into one microtask ---------------------------
export function eagerStore(onChange) {
	const state = {};
	return {
		set(key, value) {
			state[key] = value;
			onChange({ ...state }); // one render per write
		},
	};
}

export function batchedStore(onChange) {
	const state = {};
	let scheduled = false;
	return {
		set(key, value) {
			state[key] = value;
			if (scheduled) return;
			scheduled = true;
			queueMicrotask(() => {
				scheduled = false;
				onChange({ ...state }); // one render per synchronous burst
			});
		},
	};
}

// --- Yield inside long synchronous loops ---------------------------------
const mix = (h, i) => (Math.imul(h, 31) + i) | 0;

export function hashBlocking(n) {
	let h = 0;
	for (let i = 0; i < n; i++) h = mix(h, i);
	return h;
}

export async function hashYielding(n, chunk = 200_000) {
	let h = 0;
	for (let start = 0; start < n; start += chunk) {
		const end = Math.min(n, start + chunk);
		for (let i = start; i < end; i++) h = mix(h, i);
		await new Promise((resolve) => setImmediate(resolve)); // let I/O run
	}
	return h;
}

// --- Worker thread for CPU work -----------------------------------------
export function hashInWorker(n) {
	return new Promise((resolve, reject) => {
		const worker = new Worker(new URL("./cpu-worker.mjs", import.meta.url), {
			workerData: n,
		});
		worker.once("message", resolve);
		worker.once("error", reject);
	});
}

// Timer callbacks that ran while `work` was in progress.
async function timerTicksDuring(work) {
	let ticks = 0;
	const timer = setInterval(() => ticks++, 2);
	await sleep(10);
	ticks = 0;
	const result = await work();
	const observed = ticks;
	clearInterval(timer);
	return { result, ticks: observed };
}

// Longest event-loop delay (ms) observed while `work` ran.
export async function maxLoopDelayMs(work) {
	const histogram = monitorEventLoopDelay({ resolution: 1 });
	histogram.enable(); // no reset(): on node 26.8.2 a reset right before
	await sleep(5); // the work hid the blocked interval from max
	await work();
	await sleep(5); // let the sampler record the last delay
	histogram.disable();
	return histogram.max / 1e6; // histogram values are nanoseconds
}

// --- Transfer instead of copy -------------------------------------------
export function send(buffer, transfer) {
	const { port1, port2 } = new MessageChannel();
	return new Promise((resolve) => {
		port2.once("message", (received) => {
			port1.close();
			port2.close();
			resolve(received);
		});
		port1.postMessage(buffer, transfer ? [buffer] : []);
	});
}

// --- Streams: pipeline honours backpressure -----------------------------
const CHUNK = 1024;
function source(chunks) {
	let i = 0;
	return new Readable({
		read() {
			this.push(i < chunks ? Buffer.alloc(CHUNK, i++ & 255) : null);
		},
	});
}

function slowSink(stats) {
	return new Writable({
		highWaterMark: 4 * CHUNK,
		write(chunk, _encoding, callback) {
			stats.bytes += chunk.length;
			stats.peak = Math.max(stats.peak, this.writableLength);
			setImmediate(callback); // a consumer slower than the producer
		},
	});
}

export async function baselineCopy(chunks) {
	const stats = { bytes: 0, peak: 0 };
	const sink = slowSink(stats);
	const input = source(chunks);
	await new Promise((resolve, reject) => {
		input.on("data", (chunk) => sink.write(chunk)); // ignores false
		input.on("end", () => sink.end());
		sink.on("finish", resolve);
		sink.on("error", reject);
	});
	return stats;
}

export async function candidateCopy(chunks) {
	const stats = { bytes: 0, peak: 0 };
	await pipeline(source(chunks), slowSink(stats));
	return stats;
}

export async function verify() {
	const load = (id) => sleep(20, id * 2);
	let start = performance.now();
	const sequential = await baselineFetchAll([1, 2, 3, 4, 5], load);
	const sequentialMs = performance.now() - start;
	start = performance.now();
	const concurrent = await candidateFetchAll([1, 2, 3, 4, 5], load);
	const concurrentMs = performance.now() - start;
	equal("promise-all", sequential, concurrent);
	console.log(
		`TIME promise-all: ${sequentialMs.toFixed(0)} ms -> ` +
			`${concurrentMs.toFixed(0)} ms (5 x 20 ms waits)`,
	);
	ok("promise-all", concurrentMs * 2.5 < sequentialMs, "not overlapped");
	const failures = [];
	await Promise.allSettled([
		candidateFetchAll([1, 2], async (id) => {
			if (id === 1) throw new Error("first");
			return id;
		}),
	]).then(([r]) => failures.push(r.status));
	equal("promise-all rejects on first failure", failures, ["rejected"]);

	let saved = 0;
	const save = async () => {
		await sleep(1);
		saved++;
	};
	await brokenSaveAll([1, 2], save);
	equal("forEach-async returns early (hazard)", 0, saved);
	await sleep(10); // drain the abandoned callbacks
	saved = 0;
	await fixedSaveAll([1, 2], save);
	equal("for-of await", saved, 2);

	let active = 0;
	let peak = 0;
	const results = await mapLimit([5, 1, 3, 2, 4], 2, async (ms, i) => {
		active++;
		peak = Math.max(peak, active);
		await sleep(ms);
		active--;
		return i;
	});
	equal("bounded-concurrency order", results, [0, 1, 2, 3, 4]);
	equal("bounded-concurrency peak", peak, 2);
	equal("bounded-concurrency empty", await mapLimit([], 3, sleep), []);

	const ticks = {
		direct: await ticksToSettle(getValue),
		wrapped: await ticksToSettle(wrappedValue),
		chained: await ticksToSettle(chainedValue),
		returnAwait: await ticksToSettle(returnAwait),
	};
	console.log(`TICKS ${JSON.stringify(ticks)}`);
	equal("async-wrapper value", await wrappedValue(), await getValue());
	ok("async-wrapper", ticks.direct < ticks.wrapped, "wrapper not slower");
	ok("async-wrapper", ticks.direct < ticks.chained, "chain not slower");
	equal("return-await", await returnAwait(), "handled");
	let escaped = "no";
	await returnWithoutAwait().catch(() => (escaped = "yes"));
	equal("return without await escapes try (hazard)", escaped, "yes");

	const eagerRenders = [];
	const batchedRenders = [];
	const eager = eagerStore((s) => eagerRenders.push(s));
	const batched = batchedStore((s) => batchedRenders.push(s));
	for (const [k, v] of [
		["a", 1],
		["b", 2],
		["a", 3],
	]) {
		eager.set(k, v);
		batched.set(k, v);
	}
	equal("batch-microtasks before flush", batchedRenders.length, 0);
	await null;
	equal(
		"batch-microtasks final state",
		batchedRenders.at(-1),
		eagerRenders.at(-1),
	);
	console.log(
		`RENDERS batch-microtasks: ${eagerRenders.length} -> ` +
			`${batchedRenders.length}`,
	);
	equal("batch-microtasks renders", batchedRenders.length, 1);

	const N = 30_000_000;
	const blocked = await timerTicksDuring(async () => hashBlocking(N));
	const yielded = await timerTicksDuring(() => hashYielding(N));
	const offloaded = await timerTicksDuring(() => hashInWorker(N));
	equal("yield-loop result", yielded.result, blocked.result);
	equal("worker result", offloaded.result, blocked.result);
	console.log(
		`TICKS timer during CPU work: blocking ${blocked.ticks}, ` +
			`yielding ${yielded.ticks}, worker ${offloaded.ticks}`,
	);
	ok(
		"yield-loop",
		blocked.ticks === 0 && yielded.ticks > 0,
		"yielding loop did not let timers run",
	);
	ok("worker", offloaded.ticks > blocked.ticks, "worker blocked the loop");
	// Best of 3 per variant: one busy moment on a shared machine can inflate
	// a single max-delay sample for either variant. The work is 10x larger
	// than above because at N the blocked interval (about 30 ms) was no longer
	// than one descheduling pause on a loaded host (about 20 ms observed), so
	// a pause during the yielding run could erase the difference.
	const DELAY_N = 10 * N;
	const bestOf3 = async (work) => {
		let best = Number.POSITIVE_INFINITY;
		for (let i = 0; i < 3; i++) best = Math.min(best, await maxLoopDelayMs(work));
		return best;
	};
	const blockedDelay = await bestOf3(async () => hashBlocking(DELAY_N));
	const yieldedDelay = await bestOf3(() => hashYielding(DELAY_N));
	console.log(
		`DELAY max event-loop delay: blocking ` +
			`${blockedDelay.toFixed(1)} ms -> yielding ${yieldedDelay.toFixed(1)} ms`,
	);
	ok(
		"event-loop-delay",
		yieldedDelay * 2 < blockedDelay,
		"chunking did not lower the max event-loop delay",
	);

	const buffer = new Uint8Array(1 << 20).fill(7).buffer;
	const copied = await send(buffer, false);
	equal("copy keeps sender buffer", buffer.byteLength, 1 << 20);
	const moved = await send(buffer, true);
	equal("transfer detaches sender", buffer.byteLength, 0);
	equal("transfer same bytes", new Uint8Array(moved), new Uint8Array(copied));
	const big = () => new Uint8Array(32 << 20).fill(1).buffer;
	const copyStart = performance.now();
	await send(big(), false);
	const copyMs = performance.now() - copyStart;
	const moveStart = performance.now();
	await send(big(), true);
	const moveMs = performance.now() - moveStart;
	console.log(
		`TIME postMessage 32 MiB (incl. fill): copy ` +
			`${copyMs.toFixed(1)} ms -> transfer ${moveMs.toFixed(1)} ms`,
	);

	const naive = await baselineCopy(200);
	const piped = await candidateCopy(200);
	equal("pipeline bytes", piped.bytes, naive.bytes);
	console.log(
		`PEAK buffered bytes: write loop ${naive.peak} -> ` +
			`pipeline ${piped.peak}`,
	);
	ok("pipeline", piped.peak <= 4 * CHUNK, "pipeline exceeded highWaterMark");
	ok("pipeline", naive.peak > 10 * piped.peak, "baseline did not buffer");
}

// Async pairs are measured by verify(); the synchronous harness would only
// time promise creation, so this module has no bench entries.
export const benches = [];
