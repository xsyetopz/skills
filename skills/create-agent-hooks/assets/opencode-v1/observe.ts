import type { Plugin } from "@opencode-ai/plugin";

// Copy to .opencode/plugins/observe.ts. This is a registration fixture, not a gate.
// Native reference: https://opencode.ai/docs/plugins/ (checked 2026-09-15).
export const Observe: Plugin = async () => ({
  "tool.execute.after": async (_input, _output) => {
    // Intentionally no logging, mutation, network call, or stdout output.
  },
});
