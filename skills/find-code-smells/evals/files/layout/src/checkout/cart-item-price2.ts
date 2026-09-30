export function cartItemPrice(
	unitCents: number,
	quantity: number,
	discount: number,
): number {
	return unitCents * quantity - discount;
}
