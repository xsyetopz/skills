// `browser` entry: web extension host (a web worker, no Node APIs).
import * as vscode from "vscode";
import { activateCommon, settingOwner, type TodoOwnerApi } from "./common";

export function activate(context: vscode.ExtensionContext): TodoOwnerApi {
	const log = vscode.window.createOutputChannel("TODO Owner", { log: true });
	context.subscriptions.push(
		log,
		vscode.commands.registerCommand("todoOwner.ownerFromGit", () => {
			void vscode.window.showInformationMessage(
				"Reading git is not available in the browser.",
			);
			return undefined;
		}),
	);
	log.info(`activated in ${vscode.env.appHost}`);
	return activateCommon(context, log, async (doc) => settingOwner(doc));
}
