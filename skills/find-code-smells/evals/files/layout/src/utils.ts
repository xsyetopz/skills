export function formatMoney(cents: number): string {
	return `${Math.trunc(cents / 100)}.${String(cents % 100).padStart(2, "0")}`;
}

export function slugify(title: string): string {
	return title
		.toLowerCase()
		.replace(/[^a-z0-9]+/g, "-")
		.replace(/^-|-$/g, "");
}

export function sleep(ms: number): Promise<void> {
	return new Promise((resolve) => setTimeout(resolve, ms));
}
