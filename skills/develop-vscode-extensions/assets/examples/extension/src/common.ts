// Shared by the Node (`main`) and browser (`browser`) entries. Imports
// only "vscode" and ./core, so esbuild can bundle it for a web worker.
import * as vscode from "vscode";
import {
	findUnownedTodos,
	ownerSuffix,
	parseSeverity,
	RequestGenerations,
	trailingWhitespace,
} from "./core";

const SECTION = "todoOwner";
const TOKEN_KEY = "todoOwner.apiToken";
// Name every scheme: without one the host logs "uses a document selector
// without scheme" and the provider also runs on output, git, and settings
// documents. vscode-vfs is the virtual-workspace scheme (GitHub
// Repositories); the lint only needs text, so it works there too.
const SCHEMES = ["file", "untitled", "vscode-vfs"];
const SELECTOR: vscode.DocumentSelector = ["plaintext", "markdown"].flatMap(
	(language) => SCHEMES.map((scheme) => ({ language, scheme })),
);
const ours = (document: vscode.TextDocument): boolean =>
	vscode.languages.match(SELECTOR, document) > 0;

/** Returned from activate(); other extensions and tests can call it. */
export interface TodoOwnerApi {
	hasApiToken(): Promise<boolean>;
}

const SEVERITY = {
	error: vscode.DiagnosticSeverity.Error,
	warning: vscode.DiagnosticSeverity.Warning,
	information: vscode.DiagnosticSeverity.Information,
	hint: vscode.DiagnosticSeverity.Hint,
} as const;

function lint(
	document: vscode.TextDocument,
	diagnostics: vscode.DiagnosticCollection,
): number {
	const config = vscode.workspace.getConfiguration(SECTION, document);
	if (!ours(document) || !config.get<boolean>("enable", true)) {
		diagnostics.delete(document.uri);
		return 0;
	}
	const severity = SEVERITY[parseSeverity(config.get("severity"))];
	const found = findUnownedTodos(document.getText()).map((f) => {
		const range = new vscode.Range(f.line, f.start, f.line, f.end);
		const d = new vscode.Diagnostic(range, "TODO has no owner", severity);
		d.source = "todo-owner";
		d.code = "unowned-todo";
		return d;
	});
	diagnostics.set(document.uri, found);
	return found.length;
}

function ownerEdit(
	document: vscode.TextDocument,
	ranges: readonly vscode.Range[],
	owner: string,
): vscode.WorkspaceEdit {
	const edit = new vscode.WorkspaceEdit();
	const suffix = ownerSuffix(owner);
	for (const range of ranges) {
		edit.insert(document.uri, range.end, suffix);
	}
	return edit;
}

class AddOwnerAction implements vscode.CodeActionProvider {
	static readonly kinds = [vscode.CodeActionKind.QuickFix];

	provideCodeActions(
		document: vscode.TextDocument,
		_range: vscode.Range,
		context: vscode.CodeActionContext,
	): vscode.CodeAction[] {
		return context.diagnostics
			.filter((d) => d.code === "unowned-todo")
			.map((d) => {
				const action = new vscode.CodeAction(
					"Add owner",
					vscode.CodeActionKind.QuickFix,
				);
				action.diagnostics = [d];
				action.command = {
					command: "todoOwner.addOwner",
					title: "Add owner",
					arguments: [document.uri, d.range],
				};
				return action;
			});
	}
}

export function activateCommon(
	context: vscode.ExtensionContext,
	log: vscode.LogOutputChannel,
	resolveOwner: (doc: vscode.TextDocument) => Promise<string | undefined>,
): TodoOwnerApi {
	const diagnostics = vscode.languages.createDiagnosticCollection(SECTION);
	const generations = new RequestGenerations();
	context.subscriptions.push(diagnostics);

	const refreshContext = (): void => {
		const uri = vscode.window.activeTextEditor?.document.uri;
		const count = uri ? (diagnostics.get(uri)?.length ?? 0) : 0;
		void vscode.commands.executeCommand(
			"setContext",
			"todoOwner.hasFindings",
			count > 0,
		);
	};
	const relint = (document: vscode.TextDocument): void => {
		const count = lint(document, diagnostics);
		log.debug(`lint ${document.uri.toString()} v${document.version}`, count);
		refreshContext();
	};

	vscode.workspace.textDocuments.forEach(relint);
	context.subscriptions.push(
		vscode.workspace.onDidOpenTextDocument(relint),
		vscode.workspace.onDidChangeTextDocument((e) => {
			if (e.contentChanges.length > 0) relint(e.document);
		}),
		vscode.workspace.onDidCloseTextDocument((document) => {
			diagnostics.delete(document.uri);
			generations.forget(document.uri.toString());
		}),
		vscode.workspace.onWillSaveTextDocument((e) => {
			// Save events fire for every document, settings.json included.
			if (!ours(e.document)) return;
			const config = vscode.workspace.getConfiguration(SECTION, e.document);
			if (!config.get<boolean>("trimTrailingWhitespaceOnSave", true)) return;
			const edits = trailingWhitespace(e.document.getText()).map((r) =>
				vscode.TextEdit.delete(
					new vscode.Range(r.line, r.start, r.line, r.end),
				),
			);
			// Must be called synchronously during event dispatch.
			e.waitUntil(Promise.resolve(edits));
		}),
		vscode.workspace.onDidSaveTextDocument((document) => {
			if (!ours(document)) return;
			log.info(`saved ${document.uri.toString()} v${document.version}`);
		}),
		vscode.workspace.onDidChangeConfiguration((e) => {
			if (!e.affectsConfiguration(SECTION)) return;
			log.info("configuration changed; relinting open documents");
			vscode.workspace.textDocuments.forEach(relint);
		}),
		vscode.window.onDidChangeActiveTextEditor(refreshContext),
		vscode.languages.registerCodeActionsProvider(
			SELECTOR,
			new AddOwnerAction(),
			{ providedCodeActionKinds: AddOwnerAction.kinds },
		),
	);

	const applyOwner = async (
		document: vscode.TextDocument,
		ranges: readonly vscode.Range[],
	): Promise<boolean> => {
		const key = document.uri.toString();
		const generation = generations.start(key);
		const version = document.version;
		const owner = await resolveOwner(document);
		const current = vscode.workspace.textDocuments.find(
			(d) => d.uri.toString() === key,
		);
		if (!generations.isCurrent(key, generation, version, current?.version)) {
			log.warn(`discarded stale owner edit for ${key} v${version}`);
			return false;
		}
		if (!owner) {
			void vscode.window.showWarningMessage(
				"Set todoOwner.defaultOwner to add owners.",
			);
			return false;
		}
		return vscode.workspace.applyEdit(ownerEdit(document, ranges, owner));
	};

	context.subscriptions.push(
		vscode.commands.registerCommand(
			"todoOwner.encodeJsonStrings",
			async (): Promise<boolean> => {
				const editor = vscode.window.activeTextEditor;
				if (!editor) return false;
				const selections = editor.selections.filter((s) => !s.isEmpty);
				if (selections.length === 0) return false;
				// One edit() call is one undo step.
				return editor.edit((builder) => {
					for (const selection of selections) {
						const text = editor.document.getText(selection);
						builder.replace(selection, JSON.stringify(text));
					}
				});
			},
		),
		vscode.commands.registerCommand(
			"todoOwner.addOwner",
			async (uri: vscode.Uri, range: vscode.Range): Promise<boolean> => {
				const document = await vscode.workspace.openTextDocument(uri);
				return applyOwner(document, [range]);
			},
		),
		vscode.commands.registerCommand(
			"todoOwner.addOwnerToAll",
			async (): Promise<boolean> => {
				const document = vscode.window.activeTextEditor?.document;
				if (!document) return false;
				const ranges = (diagnostics.get(document.uri) ?? []).map(
					(d) => d.range,
				);
				return ranges.length > 0 && applyOwner(document, ranges);
			},
		),
		vscode.commands.registerCommand(
			"todoOwner.setApiToken",
			async (value?: string): Promise<void> => {
				const token =
					value ??
					(await vscode.window.showInputBox({
						prompt: "API token",
						password: true,
						ignoreFocusOut: true,
					}));
				if (!token) return;
				await context.secrets.store(TOKEN_KEY, token);
				log.info("API token stored"); // never log the value
			},
		),
		vscode.commands.registerCommand(
			"todoOwner.clearApiToken",
			async (): Promise<void> => {
				await context.secrets.delete(TOKEN_KEY);
				log.info("API token deleted");
			},
		),
		vscode.commands.registerCommand("todoOwner.showLog", () => log.show()),
	);

	return {
		hasApiToken: async () =>
			(await context.secrets.get(TOKEN_KEY)) !== undefined,
	};
}

export function settingOwner(doc: vscode.TextDocument): string | undefined {
	const owner = vscode.workspace
		.getConfiguration(SECTION, doc)
		.get<string>("defaultOwner", "");
	return owner.trim() === "" ? undefined : owner;
}
