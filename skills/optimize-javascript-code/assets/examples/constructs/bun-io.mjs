// Bun-only file APIs. Run: bun bun-io.mjs. Copies a 32 MiB file with
// node:fs read+write (baseline) and Bun.write(dest, Bun.file(src))
// (candidate), then checks the bytes and prints both timings.
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { readFile, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { equal, ok } from "./check.mjs";

export async function baselineCopy(src, dest) {
	await writeFile(dest, await readFile(src)); // whole file through JS heap
}

export async function candidateCopy(src, dest) {
	await Bun.write(dest, Bun.file(src)); // file-to-file, no JS buffer
}

const dir = mkdtempSync(join(tmpdir(), "bun-io-"));
try {
	const src = join(dir, "src.bin");
	const bytes = new Uint8Array(32 << 20);
	for (let i = 0; i < bytes.length; i += 4096) bytes[i] = i & 255;
	writeFileSync(src, bytes);
	const time = async (fn, dest) => {
		const start = performance.now();
		await fn(src, join(dir, dest));
		return performance.now() - start;
	};
	const results = { baseline: [], candidate: [] };
	for (let round = 0; round < 5; round++) {
		results.baseline.push(await time(baselineCopy, `b${round}.bin`));
		results.candidate.push(await time(candidateCopy, `c${round}.bin`));
	}
	equal(
		"bun-write bytes",
		readFileSync(join(dir, "b0.bin")),
		readFileSync(join(dir, "c0.bin")),
	);
	equal("bun-file size", Bun.file(src).size, bytes.length);
	const median = (xs) => xs.sort((a, b) => a - b)[2];
	const before = median(results.baseline);
	const after = median(results.candidate);
	console.log(
		`TIME copy 32 MiB median of 5: readFile+writeFile ` +
			`${before.toFixed(1)} ms -> Bun.write ${after.toFixed(1)} ms`,
	);
	ok("bun-write", after < before, "Bun.write was not faster here");
	console.log("PASS bun-io");
} finally {
	rmSync(dir, { recursive: true, force: true });
}
