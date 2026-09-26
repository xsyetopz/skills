// Explicit is better than implicit: `??` replaces only null and
// undefined; `||` also replaces 0, "", and false.
import assert from "node:assert/strict";

interface RetryOptions {
	retries?: number;
	label?: string;
}

export function effectiveRetries(options: RetryOptions): number {
	return options.retries ?? 3;
}

function effectiveRetriesImplicit(options: RetryOptions): number {
	return options.retries || 3;
}

assert.equal(effectiveRetries({}), 3);
assert.equal(effectiveRetries({ retries: 0 }), 0);
assert.equal(effectiveRetriesImplicit({ retries: 0 }), 3); // the defect
console.log("explicit: retries 0 kept with ??; || turned it into 3");
