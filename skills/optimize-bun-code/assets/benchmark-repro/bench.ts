const mode = Bun.argv[2];
const verify = Bun.argv[3] === "--verify";
const size = Number.parseInt(Bun.env.WORKLOAD_SIZE ?? "30000", 10);
const values = Array.from(
	{ length: size },
	(_, index) => `key-${index % 1200}`,
);

function red(input: string[]): Map<string, number> {
	const counts: [string, number][] = [];
	for (const value of input) {
		const found = counts.find((entry) => entry[0] === value);
		if (found) found[1] += 1;
		else counts.push([value, 1]);
	}
	return new Map(counts);
}

function green(input: string[]): Map<string, number> {
	const counts = new Map<string, number>();
	for (const value of input) counts.set(value, (counts.get(value) ?? 0) + 1);
	return counts;
}

if ((mode !== "red" && mode !== "green") || (Bun.argv[3] && !verify)) {
  throw new Error("usage: bun bench.ts red|green [--verify]");
}
const result = mode === "red" ? red(values) : green(values);
if (verify) {
	console.log(
		JSON.stringify(
			[...result.entries()].sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0)),
		),
	);
  process.exit(0);
}
const checksum = [...result.entries()].reduce(
	(total, [key, count]) => total + key.length * count,
	0,
);
console.log(JSON.stringify({ distinct: result.size, checksum }));
