// Profiling target with two obvious hot spots:
// - CPU: baselineEvenSquares runs in a loop for about 300 ms;
// - heap: retainRows keeps about 8 MiB of objects alive until exit (a
//   sampling heap profile reports only allocations still live when the
//   profile is written).
import { baselineEvenSquares } from "./allocation.mjs";

const data = Array.from({ length: 256 }, (_, i) => i);
const end = performance.now() + 300;
let sink = 0;
while (performance.now() < end) sink += baselineEvenSquares(data) & 1;

function retainRows(count) {
	const rows = [];
	for (let i = 0; i < count; i++) rows.push({ id: i, label: `row-${i}` });
	return rows;
}
globalThis.retained = retainRows(100_000);
console.log(`workload done (${sink}, ${globalThis.retained.length} rows)`);
