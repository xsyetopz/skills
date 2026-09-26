import { subtotal, type LineItem } from "./price.ts";

export function withDiscount(items: readonly LineItem[], pct: number): number {
	const base = subtotal(items);
	return base - Math.floor((base * pct) / 100);
}
