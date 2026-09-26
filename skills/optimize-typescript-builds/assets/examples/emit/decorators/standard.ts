// TC39 standard decorator (TypeScript 5.0+ without experimentalDecorators).
// --target es2022..es2025 lowers it to __esDecorate/__runInitializers;
// --target esnext emits `@logged` verbatim, which Node 26 cannot parse.
const calls: string[] = [];

function logged<This, Args extends unknown[], R>(
  method: (this: This, ...args: Args) => R,
  context: ClassMethodDecoratorContext<This>,
): (this: This, ...args: Args) => R {
  const name = String(context.name);
  return function (this: This, ...args: Args): R {
    calls.push(name);
    return method.apply(this, args);
  };
}

export class Service {
  @logged
  total(values: number[]): number {
    return values.reduce((sum, value) => sum + value, 0);
  }
}

export function run(): string {
  const result = new Service().total([1, 2, 3]);
  return `${result}:${calls.join(",")}`;
}
