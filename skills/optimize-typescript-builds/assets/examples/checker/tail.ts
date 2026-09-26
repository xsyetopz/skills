// Candidate: an accumulator parameter puts the recursive call in tail
// position, which TypeScript 4.5+ evaluates without the shallow depth limit.
type Len<S extends string, A extends 0[] = []> = S extends `${string}${infer R}`
  ? Len<R, [0, ...A]>
  : A;

type Digits = "0123456789";
type S100 = `${Digits}${Digits}${Digits}${Digits}${Digits}${Digits}${Digits}${Digits}${Digits}${Digits}`;

export const length: Len<S100>["length"] = 100;
