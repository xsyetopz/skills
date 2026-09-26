// V8-internal evidence for the shape, elements, string, and try/catch cards.
// Test-only: needs `node --allow-natives-syntax`; bun rejects `%` syntax.
// The % functions are V8 test intrinsics (FOR_EACH_INTRINSIC_TEST in
// src/runtime/runtime.h); names were confirmed on node 26.8.2 / V8 14.6.

import { concatCsv, parseAllOrNull } from "./allocation.mjs";
import { equal } from "./check.mjs";
import {
	baselineClear,
	baselineCounts,
	baselineReadings,
	baselineRecords,
	baselineSquares,
	candidateClear,
	candidateRecords,
	candidateSquares,
	mixedShapes,
	Point,
} from "./shapes.mjs";

const sameMap = (objects) =>
  objects.every((o) => %HaveSameMap(o, objects[0]));

function distinctMaps(objects) {
	const reps = [];
	for (const o of objects) {
		if (!reps.some((r) => %HaveSameMap(r, o))) reps.push(o);
	}
	return reps.length;
}

const values = [1, 2, 3, 4];
equal(
	"constructor-init baseline shapes",
	false,
	sameMap(baselineRecords(values)),
);
equal(
	"constructor-init candidate shapes",
	true,
	sameMap(candidateRecords(values)),
);

equal("avoid-delete baseline fast", false,
  %HasFastProperties(baselineClear({ id: 1, token: "t" })));
equal("avoid-delete candidate fast", true,
  %HasFastProperties(candidateClear({ id: 1, token: "t" })));

const mixed = mixedShapes(10);
equal("monomorphic baseline maps", 5, distinctMaps(mixed));
equal(
	"monomorphic candidate maps",
	1,
	distinctMaps(mixed.map((p) => new Point(p.x, p.y))),
);

equal("packed-array baseline holey", true,
  %HasHoleyElements(baselineSquares(8)));
equal("packed-array candidate holey", false,
  %HasHoleyElements(candidateSquares(8)));
// Since the 2025-02-28 update to the elements-kinds post, fill() is an
// exception to "holey forever".
equal("packed-array new Array(n).fill(0)", false,
  %HasHoleyElements(new Array(8).fill(0)));
const smis = [1, 2, 3];
equal("elements-kind smi", true, %HasSmiElements(smis));
smis.push(-0);
equal("elements-kind -0 makes doubles", true, %HasDoubleElements(smis));
equal("elements-kind null makes generic", true,
  %HasObjectElements(baselineReadings(["1", "", "2"])));

const words = Array.from({ length: 2_000 }, (_, i) => `k${i}`);
equal("dynamic keys object is dictionary", false,
  %HasFastProperties(baselineCounts(words)));

const csv = concatCsv(Array.from({ length: 50 }, (_, i) => `w${i}`));
equal("string-concat builds a rope", false, %StringIsFlat(csv));
csv.charCodeAt(0); // first indexed read flattens once
equal("string-concat flattened on read", true, %StringIsFlat(csv));

%PrepareFunctionForOptimization(parseAllOrNull)
parseAllOrNull(['{"a":1}', "x"]);
parseAllOrNull(["1", "y"]);
%OptimizeFunctionOnNextCall(parseAllOrNull)
parseAllOrNull(["2", "z"]);
const TURBOFANNED = 1 << 5; // OptimizationStatus::kTurboFanned
equal("try-catch function is TurboFan-optimized", true,
  (%GetOptimizationStatus(parseAllOrNull) & TURBOFANNED) !== 0);

console.log("PASS v8-probes");
