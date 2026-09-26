// Pure logic: no "vscode" import, so `bun test` runs it without a host.

export interface Finding {
	line: number;
	start: number;
	end: number;
}

export type SeverityName = "error" | "warning" | "information" | "hint";

const TODO = /\bTODO\b(?!\()/g;

/** Every `TODO` that is not followed by `(owner)`. */
export function findUnownedTodos(text: string): Finding[] {
	const findings: Finding[] = [];
	text.split(/\r?\n/).forEach((lineText, line) => {
		for (const match of lineText.matchAll(TODO)) {
			const start = match.index;
			findings.push({ line, start, end: start + match[0].length });
		}
	});
	return findings;
}

/** Text inserted right after `TODO` to give it an owner. */
export function ownerSuffix(owner: string): string {
	const clean = owner.trim();
	if (!/^[\w.-]+$/.test(clean)) {
		throw new Error(`invalid owner: ${JSON.stringify(owner)}`);
	}
	return `(${clean})`;
}

/** Trailing-whitespace ranges on lines that contain TODO. */
export function trailingWhitespace(text: string): Finding[] {
	const ranges: Finding[] = [];
	text.split(/\r?\n/).forEach((lineText, line) => {
		const match = /[ \t]+$/.exec(lineText);
		if (match && lineText.includes("TODO")) {
			ranges.push({ line, start: match.index, end: lineText.length });
		}
	});
	return ranges;
}

const SEVERITIES: readonly SeverityName[] = [
	"error",
	"warning",
	"information",
	"hint",
];

/** Unknown values from a hand-edited settings.json fall back. */
export function parseSeverity(value: unknown): SeverityName {
	return SEVERITIES.find((name) => name === value) ?? "warning";
}

/**
 * Stale-result guard: a result computed for document version N is
 * published only if the document is still at version N and no newer
 * request for the same key started meanwhile.
 */
export class RequestGenerations {
	private readonly latest = new Map<string, number>();

	start(key: string): number {
		const next = (this.latest.get(key) ?? 0) + 1;
		this.latest.set(key, next);
		return next;
	}

	isCurrent(
		key: string,
		generation: number,
		startedVersion: number,
		currentVersion: number | undefined,
	): boolean {
		return (
			this.latest.get(key) === generation && currentVersion === startedVersion
		);
	}

	forget(key: string): void {
		this.latest.delete(key);
	}
}

/** True when no workspace folder uses the local `file` scheme. */
export function isVirtualWorkspace(schemes: readonly string[]): boolean {
	return schemes.length > 0 && schemes.every((s) => s !== "file");
}
