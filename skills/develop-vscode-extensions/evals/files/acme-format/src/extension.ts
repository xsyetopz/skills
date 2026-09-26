import * as vscode from "vscode";
import { formatAcme } from "./format";

export function activate(context: vscode.ExtensionContext): void {
	context.subscriptions.push(
		vscode.commands.registerCommand("acme.format", async () => {
			const editor = vscode.window.activeTextEditor;
			if (!editor) {
				return;
			}
			const doc = editor.document;
			const full = new vscode.Range(
				doc.positionAt(0),
				doc.positionAt(doc.getText().length),
			);
			await editor.edit((b) => b.replace(full, formatAcme(doc.getText())));
		}),
		vscode.commands.registerCommand("acme.formatSelection", async () => {
			const editor = vscode.window.activeTextEditor;
			if (!editor) {
				return;
			}
			await editor.edit((b) => {
				for (const s of editor.selections) {
					b.replace(s, formatAcme(editor.document.getText(s)));
				}
			});
		}),
	);
}

export function deactivate(): void {}
