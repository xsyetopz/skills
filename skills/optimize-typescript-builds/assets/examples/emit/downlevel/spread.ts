// Compiled twice: --target es2017 (object spread lowered to Object.assign)
// and --target es2018 or later (native spread).
export function merge(base: object, extra: object): object {
  return { ...base, ...extra };
}

export function run(): string {
  // An own "__proto__" key, as JSON.parse produces from untrusted input.
  const input = JSON.parse('{"__proto__": {"polluted": true}, "id": 1}');
  const merged = merge({ kind: "x" }, input) as Record<string, unknown>;
  const proto = Object.getPrototypeOf(merged) === Object.prototype;
  return JSON.stringify({
    keys: Object.keys(merged),
    plainPrototype: proto,
    polluted: merged["polluted"] ?? null,
  });
}
