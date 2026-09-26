// Compiled twice: --target es2016 (async lowered to __awaiter + generator)
// and --target es2017 or later (native async/await).
async function step(i: number): Promise<number> {
  if (i < 0) throw new RangeError("negative");
  return i & 1;
}

export async function run(n: number): Promise<number> {
  let sum = 0;
  for (let i = 0; i < n; i++) sum += await step(i);
  return sum;
}

export async function fails(): Promise<string> {
  try {
    await step(-1);
    return "no error";
  } catch (error) {
    return error instanceof RangeError ? error.message : "wrong type";
  }
}
