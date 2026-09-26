// Candidate: an `as const` object plus a derived union type. Erasable, so
// Node type stripping runs it; the emitted JavaScript is the object literal.
const Op = { Add: 0, Sub: 1, Mul: 2 } as const;
type Op = (typeof Op)[keyof typeof Op];

export function isOp(value: number): value is Op {
  return value === Op.Add || value === Op.Sub || value === Op.Mul;
}

export function run(n: number): number {
  let sum = 0;
  for (let i = 0; i < n; i++) {
    const op = i % 3;
    sum += op === Op.Add ? 1 : op === Op.Sub ? 2 : op === Op.Mul ? 3 : 0;
  }
  return sum;
}
