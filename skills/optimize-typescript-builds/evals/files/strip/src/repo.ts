// Importing this module registers the repository metrics gauge (a side
// effect), so it must only be evaluated where a repository is created.
console.log("[metrics] repo gauge registered");

export interface Repo {
	find(id: number): { id: number; role: number } | undefined;
}

export function memoryRepo(): Repo {
	const rows = new Map([
		[1, { id: 1, role: 0 }],
		[2, { id: 2, role: 1 }],
	]);
	return { find: (id) => rows.get(id) };
}
