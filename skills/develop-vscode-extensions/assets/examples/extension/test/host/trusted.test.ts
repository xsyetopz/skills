// Runs inside the Extension Development Host (label "trusted"). suite and
// test are globals from the Mocha copy that @vscode/test-cli loads.
import * as assert from "node:assert/strict";
import * as vscode from "vscode";
import type { TodoOwnerApi } from "../../src/common";

const ID = "skills-example.todo-owner";

async function until<T>(read: () => T, ok: (v: T) => boolean): Promise<T> {
	for (let i = 0; i < 100; i++) {
		const value = read();
		if (ok(value)) return value;
		await new Promise((r) => setTimeout(r, 50));
	}
	throw new Error("condition not reached in 5 s");
}

const diags = (uri: vscode.Uri) => vscode.languages.getDiagnostics(uri);
const settings = () => vscode.workspace.getConfiguration("todoOwner");

suite("todo-owner (trusted workspace)", () => {
	test("implicit activation: inactive until a command runs", async () => {
		const ext = vscode.extensions.getExtension<TodoOwnerApi>(ID);
		assert.ok(ext, "extension not loaded");
		assert.equal(ext.isActive, false);
		await vscode.commands.executeCommand("todoOwner.clearApiToken");
		assert.equal(ext.isActive, true);
	});

	test("encodeJsonStrings: one undo step, empty selection no-op", async () => {
		const doc = await vscode.workspace.openTextDocument({
			content: 'α"x\nsecond\\line\nuntouched',
			language: "plaintext",
		});
		const editor = await vscode.window.showTextDocument(doc);
		editor.selections = [
			new vscode.Selection(0, 0, 0, 3),
			new vscode.Selection(1, 0, 1, 11),
			new vscode.Selection(2, 0, 2, 0),
		];
		await vscode.commands.executeCommand("todoOwner.encodeJsonStrings");
		assert.equal(doc.getText(), '"α\\"x"\n"second\\\\line"\nuntouched');
		await vscode.commands.executeCommand("undo");
		assert.equal(doc.getText(), 'α"x\nsecond\\line\nuntouched');
		editor.selection = new vscode.Selection(0, 0, 0, 0);
		const version = doc.version;
		await vscode.commands.executeCommand("todoOwner.encodeJsonStrings");
		assert.equal(doc.version, version);
	});

	test("diagnostics follow edits and the severity setting", async () => {
		const doc = await vscode.workspace.openTextDocument({
			content: "a TODO fix\n",
			language: "plaintext",
		});
		await vscode.window.showTextDocument(doc);
		const [d] = await until(
			() => diags(doc.uri),
			(l) => l.length === 1,
		);
		assert.equal(d?.message, "TODO has no owner");
		assert.equal(d?.severity, vscode.DiagnosticSeverity.Warning);

		const target = vscode.ConfigurationTarget.Global;
		await settings().update("severity", "error", target);
		await until(
			() => diags(doc.uri)[0]?.severity,
			(s) => s === vscode.DiagnosticSeverity.Error,
		);
		await settings().update("severity", undefined, target);

		const actions = await vscode.commands.executeCommand<vscode.CodeAction[]>(
			"vscode.executeCodeActionProvider",
			doc.uri,
			d!.range,
		);
		assert.ok(actions.some((a) => a.title === "Add owner"));

		const edit = new vscode.WorkspaceEdit();
		edit.insert(doc.uri, new vscode.Position(0, 6), "(ann)");
		assert.equal(await vscode.workspace.applyEdit(edit), true);
		await until(
			() => diags(doc.uri),
			(l) => l.length === 0,
		);
	});

	test("WorkspaceEdit dirties the buffer; save runs onWillSave", async () => {
		const folder = vscode.workspace.workspaceFolders?.[0]?.uri;
		assert.ok(folder, "no workspace folder");
		const file = vscode.Uri.joinPath(folder, "notes.txt");
		const encoder = new TextEncoder();
		const initial = "TODO fix  \nTODO b\n";
		await vscode.workspace.fs.writeFile(file, encoder.encode(initial));
		const doc = await vscode.workspace.openTextDocument(file);
		await vscode.window.showTextDocument(doc);
		assert.equal(doc.isDirty, false);

		await settings().update(
			"defaultOwner",
			"ann",
			vscode.ConfigurationTarget.Global,
		);
		await until(
			() => diags(doc.uri),
			(l) => l.length === 2,
		);
		const before = doc.version;
		const applied = await vscode.commands.executeCommand<boolean>(
			"todoOwner.addOwnerToAll",
		);
		assert.equal(applied, true);
		assert.equal(doc.getText(), "TODO(ann) fix  \nTODO(ann) b\n");
		assert.equal(doc.version, before + 1);
		assert.equal(doc.isDirty, true);
		const disk = async () =>
			new TextDecoder().decode(await vscode.workspace.fs.readFile(file));
		assert.equal(await disk(), initial, "edit must not write disk");

		let saved = 0;
		const listener = vscode.workspace.onDidSaveTextDocument((d) => {
			if (d.uri.toString() === file.toString()) saved++;
		});
		assert.equal(await doc.save(), true);
		listener.dispose();
		assert.equal(doc.isDirty, false);
		assert.equal(saved, 1);
		assert.equal(await disk(), "TODO(ann) fix\nTODO(ann) b\n", "trimmed");
		await settings().update(
			"defaultOwner",
			undefined,
			vscode.ConfigurationTarget.Global,
		);
	});

	test("SecretStorage round trip through the extension API", async () => {
		const api = vscode.extensions.getExtension<TodoOwnerApi>(ID)!.exports;
		await vscode.commands.executeCommand("todoOwner.setApiToken", "t0k");
		assert.equal(await api.hasApiToken(), true);
		await vscode.commands.executeCommand("todoOwner.clearApiToken");
		assert.equal(await api.hasApiToken(), false);
	});

	test("trusted: ownerFromGit runs git and stores the owner", async () => {
		assert.equal(vscode.workspace.isTrusted, true);
		const name = await vscode.commands.executeCommand<string>(
			"todoOwner.ownerFromGit",
		);
		assert.equal(name, "Test Owner");
		assert.equal(settings().inspect("defaultOwner")?.globalValue, "Test");
	});
});
