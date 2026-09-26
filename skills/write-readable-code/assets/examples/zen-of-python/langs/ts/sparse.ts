// Sparse is better than dense: one decision per line, same behavior.
import assert from "node:assert/strict";

type Level = "error" | "warn" | "info";

function badgeDense(level: Level, count: number): string {
	return count === 0
		? ""
		: level === "error"
			? `E${count > 99 ? "99+" : count}`
			: level === "warn"
				? `W${count > 99 ? "99+" : count}`
				: `${count}`;
}

export function badge(level: Level, count: number): string {
	if (count === 0) {
		return "";
	}
	if (level === "info") {
		return String(count); // uncapped: the dense form hid this exception
	}
	const shown = count > 99 ? "99+" : String(count);
	const prefix = level === "error" ? "E" : "W";
	return prefix + shown;
}

let cases = 0;
for (const level of ["error", "warn", "info"] as const) {
	for (const count of [0, 1, 99, 100, 250]) {
		assert.equal(badge(level, count), badgeDense(level, count));
		cases++;
	}
}
console.log(`sparse: ${cases} cases match the dense version`);
