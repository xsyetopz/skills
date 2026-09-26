---
name: csv-cleaner
description: Cleans messy CSV exports.
---

# CSV cleanup

Normalize CSV exports from spreadsheets before loading them.

## Workflow

1. Detect the encoding and delimiter first ([sniffing](references/sniffing.md#detect-dialect)).
1. Normalize headers and types ([types](references/types.md#parse-dates-explicitly)).
1. Validate the row count against the source.

## References

- [Sniffing](references/sniffing.md)
