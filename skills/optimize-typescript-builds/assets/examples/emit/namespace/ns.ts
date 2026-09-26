// Baseline: a namespace with values emits an IIFE and a mutable binding.
export namespace Geometry {
  export const unit = 1;
  export function area(w: number, h: number): number {
    return w * h * unit;
  }
}

export function run(n: number): number {
  let sum = 0;
  for (let i = 0; i < n; i++) sum += Geometry.area(i, 2);
  return sum;
}
