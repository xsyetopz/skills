// JavaScriptCore-internal evidence (bun only) via the bun:jsc module.
// describe() output is a debugging string, not an API contract; the
// patterns below were confirmed on bun 1.4.2.
import { describe, isRope, numberOfDFGCompiles } from "bun:jsc";
import { concatCsv, parseAllOrNull } from "./allocation.mjs";
import { equal } from "./check.mjs";
import {
	baselineClear,
	baselineCounts,
	baselineRecords,
	candidateRecords,
} from "./shapes.mjs";

const structureId = (o) => describe(o).match(/StructureID: (\d+)/)[1];
const sameStructure = (objects) => new Set(objects.map(structureId)).size === 1;

equal(
	"constructor-init baseline structures",
	false,
	sameStructure(baselineRecords([1, 2, 3, 4])),
);
equal(
	"constructor-init candidate structures",
	true,
	sameStructure(candidateRecords([1, 2, 3, 4])),
);

// One delete gives a PropertyDeletion transition, not a dictionary.
equal(
	"avoid-delete transition",
	true,
	describe(baselineClear({ id: 1, token: "t" })).includes("PropertyDeletion"),
);
const words = Array.from({ length: 2_000 }, (_, i) => `k${i}`);
equal(
	"dynamic keys object is dictionary",
	true,
	/Dictionary/.test(describe(baselineCounts(words))),
);

const csv = concatCsv(Array.from({ length: 50 }, (_, i) => `w${i}`));
equal("string-concat builds a rope", true, isRope(csv));
csv.charCodeAt(0);
equal("string-concat flattened on read", false, isRope(csv));

for (let i = 0; i < 20_000; i++) parseAllOrNull(["1", "x"]);
equal(
	"try-catch function reached DFG",
	true,
	numberOfDFGCompiles(parseAllOrNull) > 0,
);

console.log("PASS jsc-probes");
