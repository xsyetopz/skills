// Stand-in for a module with import-time cost (config parsing, SDK init).
const counters = globalThis as { heavyLoads?: number };
counters.heavyLoads = (counters.heavyLoads ?? 0) + 1;

export interface Config {
  retries: number;
}

export const defaults: Config = { retries: 3 };
