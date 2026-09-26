# Wave 1 integration notes

- `charts` added `format_axis_label()` to `src/common.py`.
- `tables` added `format_cell()` to `src/common.py`.
- `tables` was merged second and its version of `src/common.py` replaced
  the one from `charts`, so `format_axis_label()` is gone and the charts
  tests fail on the integration branch.
- Wave 1 is being redone. `pdf` has not started.
