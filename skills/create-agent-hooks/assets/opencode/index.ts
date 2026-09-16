import { Plugin } from "@opencode-ai/plugin";

// OpenCode v2 beta (opencode2), not the v1 Plugin function interface.
// https://opencode.ai/v2/docs/build/plugins
export default Plugin.define({
  id: "local-observe",
  setup: async (ctx) => {
    await ctx.tool.hook("execute.after", async (_event) => {
      // No mutation, logging, network call, or stdout output.
    });
    // The runtime owns hook-registration cleanup. Return cleanup only for
    // additional resources created and owned by this plugin.
  },
});
