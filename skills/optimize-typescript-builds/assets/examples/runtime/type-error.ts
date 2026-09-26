// A type error that type stripping (Node) and Bun's transpiler do not report.
export function run(): number {
  const count: number = "7";
  return Number(count) + 1;
}
