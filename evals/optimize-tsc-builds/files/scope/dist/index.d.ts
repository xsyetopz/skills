// Stale output from the old tsc build (kept for the docs site).
export interface LineItem {
    sku: string;
    unitCents: number;
    qty: number;
}
export declare function subtotal(items: readonly LineItem[]): number;
export declare function withDiscount(items: readonly LineItem[], pct: number): number;
