import { execFile } from "node:child_process";
import * as vscode from "vscode";
import { hoverFor } from "./hover";

const selector: vscode.DocumentSelector = { language: "acme", scheme: "file" };

export function activate(context: vscode.ExtensionContext): void {
	const problems = vscode.languages.createDiagnosticCollection("acme");
	context.subscriptions.push(problems);

	const lint = (doc: vscode.TextDocument) => {
		if (!vscode.languages.match(selector, doc)) {
			return;
		}
		const config = vscode.workspace.getConfiguration("acme", doc.uri);
		const linter = config.get<string>("linterPath", "acme-lint");
		execFile(linter, ["--json", doc.uri.fsPath], (_err, stdout) => {
			const found: { line: number; message: string }[] = JSON.parse(
				stdout || "[]",
			);
			problems.set(
				doc.uri,
				found.map(
					(p) =>
						new vscode.Diagnostic(
							new vscode.Range(p.line, 0, p.line, 1000),
							p.message,
						),
				),
			);
		});
	};

	context.subscriptions.push(
		vscode.workspace.onDidOpenTextDocument(lint),
		vscode.workspace.onDidSaveTextDocument(lint),
		vscode.commands.registerCommand("acme.lintNow", () => {
			const doc = vscode.window.activeTextEditor?.document;
			if (doc) {
				lint(doc);
			}
		}),
		vscode.languages.registerHoverProvider(selector, {
			provideHover(doc, position) {
				return hoverFor(doc.lineAt(position.line).text);
			},
		}),
	);
	vscode.workspace.textDocuments.forEach(lint);
}

export function deactivate(): void {}
