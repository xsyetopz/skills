export interface Row {
	id: number;
	accountId: number;
	cents: number;
}

export interface Account {
	id: number;
	name: string;
}

/** Joins every row with its account name, in row order. */
export function labelRows(rows: readonly Row[], accounts: readonly Account[]): string[] {
	return rows.map((row) => {
		const account = accounts.find((a) => a.id === row.accountId);
		return `${row.id}:${account ? account.name : "?"}:${row.cents}`;
	});
}
