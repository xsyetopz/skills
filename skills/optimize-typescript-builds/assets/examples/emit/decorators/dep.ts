// Stand-in for an expensive module: records every evaluation.
const counters = globalThis as { depLoads?: number };
counters.depLoads = (counters.depLoads ?? 0) + 1;

export class Database {
  query(): number {
    return 1;
  }
}
