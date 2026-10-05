export interface LineItem {
	sku: string;
	unitCents: number;
	qty: number;
}

export function subtotal(items: readonly LineItem[]): number {
	return items.reduce((sum, item) => sum + item.unitCents * item.qty, 0);
}
