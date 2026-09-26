// Legacy parameter decorator (experimentalDecorators). With
// emitDecoratorMetadata, tsc emits __metadata("design:paramtypes",
// [Database]), which keeps the import of ./dep.ts as a runtime import.
import { Database } from "./dep.ts";

function inject(_target: object, _key: string | undefined, _i: number): void {}

export class Repository {
  private readonly db: Database;
  constructor(@inject db: Database) {
    this.db = db;
  }
  count(): number {
    return this.db.query();
  }
}

export function run(): number {
  const loads = (globalThis as { depLoads?: number }).depLoads ?? 0;
  return loads;
}
