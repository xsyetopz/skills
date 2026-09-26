// OpenCode (v1 plugin API) guard: throwing from "tool.execute.before"
// stops the tool call, as in the docs' .env protection example.
// Copy to .opencode/plugins/guard.ts. The type import is erased at run
// time, so the file loads without installing @opencode-ai/plugin.
import type { Plugin } from "@opencode-ai/plugin";

const DENY: Array<[string, RegExp]> = [
	["force push", /\bgit\s+push\b.*\s(--force|-f)(\s|$)/],
	[
		"recursive delete of / or ~",
		/\brm\s+-[a-zA-Z]*r[a-zA-Z]*f[a-zA-Z]*\s+(\/|~)(\s|$)/,
	],
];

export const GuardPlugin: Plugin = async () => ({
	"tool.execute.before": async (input, output) => {
		if (input.tool !== "bash") return;
		const command = String(output.args?.command ?? "");
		for (const [label, pattern] of DENY) {
			if (pattern.test(command)) {
				const shown = command.slice(0, 200);
				throw new Error(`Blocked by guard (${label}): ${shown}`);
			}
		}
	},
});
