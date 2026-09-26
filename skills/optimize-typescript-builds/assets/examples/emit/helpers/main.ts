import { loadA } from "./a.ts";
import { loadB } from "./b.ts";
import { loadC } from "./c.ts";

export async function run(): Promise<number> {
  const values = [1, 2, 3];
  return (await loadA(values)) + (await loadB(values)) + (await loadC(values));
}
