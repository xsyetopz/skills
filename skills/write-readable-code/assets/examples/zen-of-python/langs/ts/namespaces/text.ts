export function normalize(value: string): string {
	return value.trim().toLowerCase();
}

export function parse(value: string): string[] {
	return value.split(",").map(normalize).filter(Boolean);
}
