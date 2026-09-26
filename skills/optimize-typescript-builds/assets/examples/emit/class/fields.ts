// Candidate: explicit fields assigned in the constructor. Erasable.
export class Point {
  readonly x: number;
  readonly y: number;
  constructor(x: number, y: number) {
    this.x = x;
    this.y = y;
  }
  norm1(): number {
    return Math.abs(this.x) + Math.abs(this.y);
  }
}

export function run(n: number): number {
  let sum = 0;
  for (let i = 0; i < n; i++) sum += new Point(i, -i).norm1();
  return sum;
}
