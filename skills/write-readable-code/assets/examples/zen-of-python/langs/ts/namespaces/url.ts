export function normalize(value: string): string {
	return new URL(value).href;
}
