import * as vscode from "vscode";

export interface CheckResult {
	problems: { line: number; message: string }[];
}

// Talks to the acme-check server over HTTP on localhost; a check takes 50-800 ms.
export class CheckClient implements vscode.Disposable {
	async check(text: string): Promise<CheckResult> {
		const res = await fetch("http://127.0.0.1:7788/check", {
			method: "POST",
			body: text,
		});
		return (await res.json()) as CheckResult;
	}

	dispose(): void {}
}

export function toDiagnostics(r: CheckResult): vscode.Diagnostic[] {
	return r.problems.map(
		(p) =>
			new vscode.Diagnostic(
				new vscode.Range(p.line, 0, p.line, Number.MAX_SAFE_INTEGER),
				p.message,
			),
	);
}
