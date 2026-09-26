// `main` entry: desktop and remote Node extension hosts.
import * as vscode from "vscode";
import { activateCommon, settingOwner, type TodoOwnerApi } from "./common";
import { gitUserName } from "./node/git";

export function activate(context: vscode.ExtensionContext): TodoOwnerApi {
	const log = vscode.window.createOutputChannel("TODO Owner", { log: true });
	context.subscriptions.push(log);
	log.info(
		`activated in ${vscode.env.appHost}, trusted=` +
			`${vscode.workspace.isTrusted}`,
	);

	context.subscriptions.push(
		vscode.commands.registerCommand(
			"todoOwner.ownerFromGit",
			async (): Promise<string | undefined> => {
				// The manifest hides this command in untrusted workspaces, but
				// executeCommand and keybindings still reach it: check here too.
				if (!vscode.workspace.isTrusted) {
					log.warn("ownerFromGit refused: workspace is not trusted");
					return undefined;
				}
				const folder = vscode.workspace.workspaceFolders?.find(
					(f) => f.uri.scheme === "file",
				);
				if (!folder) return undefined;
				const gitPath = vscode.workspace
					.getConfiguration("todoOwner", folder.uri)
					.get<string>("gitPath", "git");
				const name = await gitUserName(gitPath, folder.uri.fsPath);
				if (name) {
					await vscode.workspace
						.getConfiguration("todoOwner", folder.uri)
						.update(
							"defaultOwner",
							name.split(/\s+/)[0],
							vscode.ConfigurationTarget.Global,
						);
				}
				return name;
			},
		),
	);
	return activateCommon(context, log, async (doc) => settingOwner(doc));
}

export function deactivate(): void {
	// Everything is in context.subscriptions; nothing async to await.
}
