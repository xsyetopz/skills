export function formatAcme(text: string): string {
	return text
		.split("\n")
		.map((line) => line.replace(/\s+$/, "").replace(/^\s*=\s*/, "= "))
		.join("\n");
}
