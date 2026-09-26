// Baseline: a regular enum emits an IIFE that builds a two-way object.
enum Op {
  Add,
  Sub,
  Mul,
}

export function run(n: number): number {
  let sum = 0;
  for (let i = 0; i < n; i++) {
    const op = i % 3;
    sum += op === Op.Add ? 1 : op === Op.Sub ? 2 : op === Op.Mul ? 3 : 0;
  }
  return sum;
}
