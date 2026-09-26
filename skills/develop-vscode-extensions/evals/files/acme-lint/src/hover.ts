import * as vscode from "vscode";

const KEYWORDS: Record<string, string> = {
	include: "Includes another Acme file.",
	define: "Defines a named value.",
};

export function hoverFor(line: string): vscode.Hover | undefined {
	const word = line.trim().split(/\s+/)[0];
	const text = KEYWORDS[word];
	return text ? new vscode.Hover(text) : undefined;
}
