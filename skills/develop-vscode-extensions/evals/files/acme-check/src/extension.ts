import * as vscode from "vscode";
import { CheckClient, toDiagnostics } from "./client";

export function activate(context: vscode.ExtensionContext): void {
	const server = new CheckClient();
	const collection = vscode.languages.createDiagnosticCollection("acme-check");
	context.subscriptions.push(server, collection);

	context.subscriptions.push(
		vscode.workspace.onDidChangeTextDocument(async (e) => {
			if (e.document.languageId !== "acme") {
				return;
			}
			const r = await server.check(e.document.getText());
			collection.set(e.document.uri, toDiagnostics(r));
		}),
	);
}

export function deactivate(): void {}
