// Replays the endpoint's workload: node report/replay.mjs
import { buildReport } from './report.mjs';

const rows = Array.from({ length: 1000 }, (_, i) => ({
  id: i,
  active: i % 3 !== 0,
  total: (i * 37) % 1000,
}));

let sink = 0;
const start = process.hrtime.bigint();
for (let i = 0; i < 50_000; i++) {
  sink += buildReport(rows).total;
}
const ms = Number(process.hrtime.bigint() - start) / 1e6;
console.log(`sink=${sink} elapsed=${ms.toFixed(1)} ms`);
