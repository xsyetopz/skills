# Design baseline: CSV export (frozen)

One shared formatter produces the CSV so that R4 holds by construction.

| Component | Files to create or change | Uses |
| --- | --- | --- |
| Formatter | `src/export/formatter.py`, `tests/test_formatter.py` | nothing |
| API | `src/api/export_routes.py`, `src/api/routes.py`, `tests/test_api_export.py` | formatter |
| CLI | `src/cli/export_cmd.py`, `tests/test_cli_export.py` | formatter |
| Web | `web/src/ExportButton.tsx`, `web/tests/ExportButton.test.tsx` | the API URL from R1 only |

Interface: `format_rows(columns: list[str], rows: list[list[str]]) -> str`
in `src/export/formatter.py`. The web button links to the R1 URL and does
not import Python code.
