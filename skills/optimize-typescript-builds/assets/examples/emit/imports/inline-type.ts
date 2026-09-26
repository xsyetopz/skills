// Baseline: an inline `type` specifier. Under verbatimModuleSyntax (and in
// Node type stripping) this becomes `import {} from "./heavy.ts"`, so the
// module still evaluates.
import { type Config } from "./heavy.ts";

export function run(): number {
  const config: Config = { retries: 1 };
  const loads = (globalThis as { heavyLoads?: number }).heavyLoads ?? 0;
  return config.retries * 10 + loads;
}
