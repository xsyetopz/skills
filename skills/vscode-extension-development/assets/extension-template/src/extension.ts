import * as vscode from "vscode";

export function activate(context: vscode.ExtensionContext): void {
  context.subscriptions.push(
    vscode.commands.registerCommand(
      "__EXTENSION_NAME__.encodeJsonStrings",
      async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor) return;
        const selections = editor.selections.filter(
          (selection) => !selection.isEmpty,
        );
        if (selections.length === 0) return;
        const applied = await editor.edit((builder) => {
          for (const selection of selections) {
            builder.replace(
              selection,
              JSON.stringify(editor.document.getText(selection)),
            );
          }
        });
        if (!applied) {
          await vscode.window.showWarningMessage(
            "The selected text could not be edited.",
          );
        }
      },
    ),
  );
}
