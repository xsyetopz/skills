// Config for `vscode-test` (@vscode/test-cli). verify.sh sets the env
// variables. Profile directories live under TODO_OWNER_TMP so the run
// never touches the user's own VS Code profile. Keep TODO_OWNER_TMP
// short: VS Code puts a Unix socket in --user-data-dir, and macOS
// rejects socket paths longer than 103 characters.
import { defineConfig } from "@vscode/test-cli";

const tmp = process.env.TODO_OWNER_TMP;
const exe = process.env.VSCODE_TEST_EXECUTABLE;
if (!tmp) throw new Error("set TODO_OWNER_TMP to a scratch directory");

export default defineConfig({
  label: "trusted",
  files: "out/test/host/**/*.test.js",
  version: process.env.VSCODE_TEST_VERSION ?? "stable",
  ...(exe ? { useInstallation: { fromPath: exe } } : {}),
  workspaceFolder: `${tmp}/ws-t`,
  // Secrets stay in memory, never in the OS keychain. The flag is
  // --use-inmemory-secretstorage on current builds and --disable-keytar
  // on 1.74; an unknown flag swallows the next bare argument, and
  // test-cli appends the workspace folder last, so keep these first.
  launchArgs: [
    "--use-inmemory-secretstorage",
    "--disable-keytar",
    `--user-data-dir=${tmp}/t/u`,
    `--extensions-dir=${tmp}/t/x`,
    "--disable-extensions",
  ],
  env: { GIT_CONFIG_GLOBAL: `${tmp}/gitconfig`, GIT_CONFIG_NOSYSTEM: "1" },
  mocha: { ui: "tdd", timeout: 20000 },
});
