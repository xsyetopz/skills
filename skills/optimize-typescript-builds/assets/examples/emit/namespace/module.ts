// Candidate: plain module exports. Erasable; callers use
// `import * as Geometry from "./module.ts"` for the same qualified names.
export const unit = 1;
export function area(w: number, h: number): number {
  return w * h * unit;
}

export function run(n: number): number {
  let sum = 0;
  for (let i = 0; i < n; i++) sum += area(i, 2);
  return sum;
}
