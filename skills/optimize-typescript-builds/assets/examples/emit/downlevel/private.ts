// Compiled twice: --target es2021 (#count lowered to a WeakMap) and
// --target es2022 or later (native private field).
export class Counter {
  #count = 0;
  inc(): number {
    return ++this.#count;
  }
  static owns(value: object): boolean {
    return #count in value;
  }
}

export function run(n: number): number {
  const counter = new Counter();
  let odd = 0;
  for (let i = 0; i < n; i++) odd += counter.inc() & 1;
  return odd + (Counter.owns(counter) ? 1 : 0) + (Counter.owns({}) ? 1 : 0);
}
