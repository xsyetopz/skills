# Plan: CSV export

1. Slice A: add `format_rows()` in `src/export/csv.py`; done when
   `tests/test_csv.py::test_format_rows` passes.
2. Slice B: add the `--csv` flag in `src/cli.py`; done when
   `tests/test_cli.py::test_csv_flag` passes.
3. Slice C: wire the export button in `web/Export.tsx`; done when
   `web/Export.test.tsx` passes.
