// Demonstrates type-feedback pollution: one sumAll() measured on a holey
// array first and a packed array second, in one process. Compare with
// `sh verify.sh measure` (packed-array read), which isolates each side.
// Usage: node shared-feedback.mjs   (or bun)
import { measure, report } from "./bench.mjs";
import { baselineSquares, candidateSquares, sumAll } from "./shapes.mjs";

const holey = baselineSquares(4_096);
const packed = candidateSquares(4_096);
const options = { warmupMs: 300, sampleMs: 50, samples: 15 };
report(
	"holey (measured first)",
	measure(() => sumAll(holey), options),
);
report(
	"packed (measured second)",
	measure(() => sumAll(packed), options),
);
