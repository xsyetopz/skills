import * as vscode from "vscode";

function normalizeHeadings(text: string): string {
	return text.replace(/^(#+)([^#\s])/gm, "$1 $2");
}

export function activate(context: vscode.ExtensionContext): void {
	context.subscriptions.push(
		vscode.commands.registerCommand("acmeDocfmt.formatDoc", async () => {
			const editor = vscode.window.activeTextEditor;
			if (!editor) {
				return;
			}
			const doc = editor.document;
			const all = new vscode.Range(
				doc.positionAt(0),
				doc.positionAt(doc.getText().length),
			);
			await editor.edit((b) => b.replace(all, normalizeHeadings(doc.getText())));
		}),
	);
}

export function deactivate(): void {}
