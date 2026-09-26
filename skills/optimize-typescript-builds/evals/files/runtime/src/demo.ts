import { labelRows, type Account, type Row } from "./rows.ts";

const accounts: Account[] = Array.from({ length: 20_000 }, (_, i) => ({ id: i * 3, name: `acct-${i}` }));
const rows: Row[] = Array.from({ length: 50_000 }, (_, i) => ({ id: i, accountId: (i * 7) % 60_001, cents: i % 997 }));
const started = performance.now();
const labels = labelRows(rows, accounts);
console.log(labels.length, labels[1], `${Math.round(performance.now() - started)} ms`);
