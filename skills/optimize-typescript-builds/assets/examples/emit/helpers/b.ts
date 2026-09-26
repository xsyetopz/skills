// One of three modules compiled at --target es2016. Each async function needs
// the __awaiter helper: inline per file by default, imported with
// --importHelpers.
export async function loadB(values: number[]): Promise<number> {
  let sum = 0;
  for (const value of values) sum += await Promise.resolve(value);
  return sum;
}
