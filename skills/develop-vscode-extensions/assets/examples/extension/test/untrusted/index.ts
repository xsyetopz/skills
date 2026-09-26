// Extension test entry for Restricted Mode, run without @vscode/test-cli:
// runTests() in @vscode/test-electron always adds --disable-workspace-trust,
// so verify.sh starts VS Code directly with --extensionTestsPath=<this>.
// The workspace has .vscode/settings.json with todoOwner.gitPath set to a
// path that must never run. VS Code exits non-zero if run() rejects.
import * as assert from "node:assert/strict";
import * as vscode from "vscode";

export async function run(): Promise<void> {
	assert.equal(vscode.workspace.isTrusted, false, "expected Restricted Mode");

	const folder = vscode.workspace.workspaceFolders?.[0]?.uri;
	assert.ok(folder, "no workspace folder");
	const file = vscode.Uri.joinPath(folder, ".vscode", "settings.json");
	const onDisk = new TextDecoder().decode(
		await vscode.workspace.fs.readFile(file),
	);
	assert.ok(onDisk.includes("/nonexistent/evil-git"), "fixture missing");
	// restrictedConfigurations: the workspace value is withheld from both
	// get() and inspect() while the workspace is untrusted.
	const config = vscode.workspace.getConfiguration("todoOwner");
	assert.equal(config.get("gitPath"), "git");
	assert.equal(config.inspect<string>("gitPath")?.workspaceValue, undefined);

	const name = await vscode.commands.executeCommand<string | undefined>(
		"todoOwner.ownerFromGit",
	);
	assert.equal(name, undefined, "trust-gated command must refuse");
	console.log("untrusted: 3 checks passed");
}
