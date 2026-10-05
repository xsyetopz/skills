import { execFileSync } from "node:child_process";
import * as fs from "node:fs";
import * as path from "node:path";
import * as vscode from "vscode";

interface BlameConfig {
	watched: number[];
}

function readConfig(doc: vscode.TextDocument): BlameConfig {
	const dir = path.dirname(doc.uri.fsPath);
	const file = path.join(dir, ".acmeblame.json");
	if (!fs.existsSync(file)) {
		return { watched: [] };
	}
	return JSON.parse(fs.readFileSync(file, "utf8")) as BlameConfig;
}

const watchedStyle = vscode.window.createTextEditorDecorationType({
	backgroundColor: new vscode.ThemeColor("editor.wordHighlightBackground"),
});

export function activate(context: vscode.ExtensionContext): void {
	context.subscriptions.push(
		watchedStyle,
		vscode.commands.registerCommand("acmeBlame.showLineAuthor", () => {
			const editor = vscode.window.activeTextEditor;
			if (!editor) {
				return;
			}
			const line = editor.selection.active.line + 1;
			const out = execFileSync(
				"git",
				["blame", "-L", `${line},${line}`, "--porcelain", editor.document.uri.fsPath],
				{ cwd: path.dirname(editor.document.uri.fsPath), encoding: "utf8" },
			);
			const author = /^author (.*)$/m.exec(out)?.[1] ?? "unknown";
			vscode.window.showInformationMessage(`Line ${line}: ${author}`);
		}),
		vscode.commands.registerCommand("acmeBlame.highlightWatched", () => {
			const editor = vscode.window.activeTextEditor;
			if (!editor) {
				return;
			}
			const { watched } = readConfig(editor.document);
			editor.setDecorations(
				watchedStyle,
				watched.map((n) => editor.document.lineAt(n - 1).range),
			);
		}),
	);
}

export function deactivate(): void {}
