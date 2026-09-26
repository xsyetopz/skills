// Minimal explicit-token DI container: dependencies are resolved from the
// tokens given to @Inject, never from reflected constructor types.
type Factory<T> = () => T;
type Ctor = new (...args: never[]) => unknown;

const factories = new Map<symbol, Factory<unknown>>();
const paramTokens = new Map<Ctor, symbol[]>();

export function register<T>(token: symbol, factory: Factory<T>): void {
	factories.set(token, factory);
}

export function Inject(token: symbol) {
	return (target: object, _key: string | symbol | undefined, index: number): void => {
		const tokens = paramTokens.get(target as Ctor) ?? [];
		tokens[index] = token;
		paramTokens.set(target as Ctor, tokens);
	};
}

export function Injectable() {
	return (_target: object): void => {};
}

export function resolve<T>(ctor: new (...args: any[]) => T): T {
	const tokens = paramTokens.get(ctor) ?? [];
	const args = tokens.map((token) => {
		const factory = factories.get(token);
		if (!factory) throw new Error(`no provider for ${String(token)}`);
		return factory();
	});
	return new ctor(...args);
}
