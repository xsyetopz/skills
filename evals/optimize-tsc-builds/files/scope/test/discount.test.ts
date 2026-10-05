// Plain-assert test (no @types/node needed): `node --test` fails on a throw.
import { withDiscount } from "../src/index.ts";

function equal(actual: number, expected: number): void {
	if (actual !== expected) throw new Error(`expected ${expected}, got ${actual}`);
}

equal(withDiscount([{ sku: "a", unitCents: 1000, qty: 3 }], 10), 2700);
equal(withDiscount([], 50), 0);
