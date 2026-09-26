# Requirements baseline: CSV export (frozen)

- R1: `GET /reports/{id}/export.csv` returns the report as CSV.
- R2: `reportctl export ID` writes the same CSV to stdout.
- R3: The report page has an Export button that downloads the CSV.
- R4: All three produce byte-identical CSV for the same report.
