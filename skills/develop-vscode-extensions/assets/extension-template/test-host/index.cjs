const assert = require("node:assert/strict");
const vscode = require("vscode");

exports.run = async () => {
  const document = await vscode.workspace.openTextDocument({
    content: 'α"x\nsecond\\line\nuntouched',
    language: "plaintext",
  });
  const editor = await vscode.window.showTextDocument(document);
  editor.selections = [
    new vscode.Selection(0, 0, 0, 3),
    new vscode.Selection(1, 0, 1, 11),
    new vscode.Selection(2, 0, 2, 0),
  ];
  await vscode.commands.executeCommand(
    "__EXTENSION_NAME__.encodeJsonStrings",
  );
  assert.equal(document.getText(), '"α\\"x"\n"second\\\\line"\nuntouched');
  await vscode.commands.executeCommand("undo");
  assert.equal(document.getText(), 'α"x\nsecond\\line\nuntouched');
  editor.selection = new vscode.Selection(0, 0, 0, 0);
  const version = document.version;
  await vscode.commands.executeCommand(
    "__EXTENSION_NAME__.encodeJsonStrings",
  );
  assert.equal(document.version, version);
  await vscode.commands.executeCommand(
    "workbench.action.revertAndCloseActiveEditor",
  );
};
