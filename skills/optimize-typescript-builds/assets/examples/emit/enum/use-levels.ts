import { Level } from "./levels.ts";

export function run(n: number): number {
  return n > 10 ? Level.High : Level.Low;
}
