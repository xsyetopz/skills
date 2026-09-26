// Hazard: a type imported without `type`. tsc (without
// verbatimModuleSyntax) elides it; Node type stripping keeps it and fails
// with a SyntaxError because heavy.ts exports no runtime binding `Config`.
import { Config } from "./heavy.ts";

export function run(): number {
  const config: Config = { retries: 1 };
  const loads = (globalThis as { heavyLoads?: number }).heavyLoads ?? 0;
  return config.retries * 10 + loads;
}
