// Sampling allocation profile that keeps objects already collected by GC,
// so short-lived garbage is attributed too (node --heap-prof keeps only
// live objects). Node only: bun has no node:inspector Session.
// Usage: node alloc-profile.mjs
import { Session } from "node:inspector/promises";
import { baselineEvenSquares, candidateEvenSquares } from "./allocation.mjs";

async function sampledBytes(fn) {
	const session = new Session();
	session.connect();
	await session.post("HeapProfiler.startSampling", {
		samplingInterval: 4096, // bytes between samples (default 32768)
		includeObjectsCollectedByMinorGC: true,
		includeObjectsCollectedByMajorGC: true,
	});
	const data = Array.from({ length: 256 }, (_, i) => i);
	let sink = 0;
	for (let i = 0; i < 20_000; i++) sink += fn(data) & 1;
	const { profile } = await session.post("HeapProfiler.stopSampling");
	session.disconnect();
	// Inclusive bytes under frames named fn.name (builtins such as
	// Array.prototype.map appear as child frames).
	const inclusive = (node) =>
		node.children.reduce((sum, c) => sum + inclusive(c), node.selfSize);
	let hot = 0;
	const visit = (node) => {
		if (node.callFrame.functionName === fn.name) hot += inclusive(node);
		else node.children.forEach(visit);
	};
	visit(profile.head);
	return { hot, sink };
}

const before = await sampledBytes(baselineEvenSquares);
const after = await sampledBytes(candidateEvenSquares);
console.log(
	`PROFILE sampled allocation: ${before.hot} B in ` +
		`baselineEvenSquares -> ${after.hot} B in candidateEvenSquares`,
);
if (!(after.hot * 10 < before.hot)) process.exit(1);
