// Summarizes invoice rows for the /report endpoint.
export function buildReport(rows) {
  const total = rows
    .filter((r) => r.active)
    .map((r) => r.total)
    .reduce((a, b) => a + b, 0);
  const count = rows.filter((r) => r.active).length;
  return { total, count };
}
