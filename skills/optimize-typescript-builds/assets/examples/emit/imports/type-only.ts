// Candidate: a top-level `import type` is erased entirely.
import type { Config } from "./heavy.ts";

export function run(): number {
  const config: Config = { retries: 1 };
  const loads = (globalThis as { heavyLoads?: number }).heavyLoads ?? 0;
  return config.retries * 10 + loads;
}
