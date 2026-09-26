// Baseline: the recursive call is wrapped in a tuple spread, so it is not in
// tail position; TypeScript stops at its instantiation-depth heuristic.
type Len<S extends string> = S extends `${string}${infer R}`
  ? [0, ...Len<R>]
  : [];

type Digits = "0123456789";
type S100 = `${Digits}${Digits}${Digits}${Digits}${Digits}${Digits}${Digits}${Digits}${Digits}${Digits}`;

export const length: Len<S100>["length"] = 100;
