// Baseline: parameter properties need code generation (not erasable).
export class Point {
  constructor(
    public readonly x: number,
    public readonly y: number,
  ) {}
  norm1(): number {
    return Math.abs(this.x) + Math.abs(this.y);
  }
}

export function run(n: number): number {
  let sum = 0;
  for (let i = 0; i < n; i++) sum += new Point(i, -i).norm1();
  return sum;
}
