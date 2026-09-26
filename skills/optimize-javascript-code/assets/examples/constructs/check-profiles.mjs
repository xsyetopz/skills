// Reads every profile in a directory and prints where workload.mjs's hot
// frames show up: CPU samples in baselineEvenSquares, live sampled bytes in
// retainRows. Exits 1 when a profile
// is missing, unparsable, or does not attribute cost to the hot frame.
// Usage: node check-profiles.mjs <dir>
import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";

const HOT = "baselineEvenSquares";
const RETAINER = "retainRows";
const dir = process.argv[2];
const files = readdirSync(dir);
let failures = files.length === 0 ? 1 : 0;

function* walk(node) {
	yield node;
	for (const child of node.children ?? []) yield* walk(child);
}

for (const file of files) {
	const data = JSON.parse(readFileSync(join(dir, file), "utf8"));
	let line;
	if (file.endsWith(".cpuprofile")) {
		// nodes[].hitCount = samples whose top frame was this node; inclusive
		// samples add every descendant of a node named HOT.
		const byId = new Map(data.nodes.map((n) => [n.id, n]));
		const subtree = (n) =>
			(n.hitCount ?? 0) +
			(n.children ?? []).reduce((s, id) => s + subtree(byId.get(id)), 0);
		const hotNodes = data.nodes.filter((n) => n.callFrame.functionName === HOT);
		const total = data.nodes.reduce((s, n) => s + (n.hitCount ?? 0), 0);
		const self = hotNodes.reduce((s, n) => s + (n.hitCount ?? 0), 0);
		const inclusive = hotNodes.reduce((s, n) => s + subtree(n), 0);
		line =
			`${inclusive}/${total} samples inclusive, ${self} self, ` + `in ${HOT}`;
		if (inclusive * 2 < total) failures++;
	} else if (file.endsWith(".heapprofile")) {
		// Sampling heap profile: head.children tree with selfSize bytes.
		let total = 0;
		let hot = 0;
		for (const n of walk(data.head)) {
			total += n.selfSize;
			if (n.callFrame.functionName === RETAINER) hot += n.selfSize;
		}
		line = `${hot}/${total} live sampled bytes allocated in ${RETAINER}`;
		if (hot === 0) failures++;
	} else if (file.endsWith(".heapsnapshot")) {
		line = `${data.snapshot.node_count} nodes in snapshot`;
		if (!(data.snapshot.node_count > 0)) failures++;
	} else {
		line = "unrecognized file";
		failures++;
	}
	console.log(`PROFILE ${file.replace(/[\d.]+(?=\.\w+$)/, "*")}: ${line}`);
}
process.exit(failures ? 1 : 0);
