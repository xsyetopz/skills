import { describe, expect, test } from "bun:test";
import { GuardPlugin } from "./guard.ts";

// The plugin function receives { project, client, $, directory, worktree };
// the guard uses none of them.
const hooks = await GuardPlugin({} as never);
const before = hooks["tool.execute.before"]!;

describe("guard plugin", () => {
	test("throws for a force push", async () => {
		const output = { args: { command: "git push --force origin main" } };
		await expect(
			before({ tool: "bash" } as never, output as never),
		).rejects.toThrow("force push");
	});

	test("lets other commands and tools through", async () => {
		await before(
			{ tool: "bash" } as never,
			{ args: { command: "npm test" } } as never,
		);
		await before(
			{ tool: "read" } as never,
			{ args: { filePath: "a" } } as never,
		);
	});
});
