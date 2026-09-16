import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { test } from "node:test";
import { runTests } from "@vscode/test-electron";

test("selection edits in the VS Code host", { timeout: 120_000 }, async () => {
  const profile = await mkdtemp(join(tmpdir(), "selection-host-"));
  const { VSCODE_TEST_VERSION, VSCODE_EXECUTABLE_PATH } = process.env;
  try {
    await runTests({
      version: VSCODE_TEST_VERSION ?? "__VSCODE_TEST_VERSION__",
      ...(VSCODE_EXECUTABLE_PATH
        ? { vscodeExecutablePath: VSCODE_EXECUTABLE_PATH }
        : {}),
      extensionDevelopmentPath: resolve("."),
      extensionTestsPath: resolve("test-host/index.cjs"),
      launchArgs: [
        `--user-data-dir=${join(profile, "data")}`,
        `--extensions-dir=${join(profile, "extensions")}`,
        "--disable-extensions",
        "--skip-welcome",
        "--skip-release-notes",
        "--disable-updates",
      ],
    });
  } finally {
    await rm(profile, { recursive: true, force: true });
  }
});
