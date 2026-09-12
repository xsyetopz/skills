import { Plugin } from "@opencode/plugin";

export default Plugin.define({
	id: "harmless-hook-observer",
	async setup(ctx) {
		const registration = await ctx.tool.hook("execute.after", () => {
			// Intentionally no side effect: this fixture proves hook registration.
		});
		return () => registration.dispose();
	},
});
