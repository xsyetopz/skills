# Worked scenarios for Git Regression Search

## Oracle exit contract

```text
0   behavior is good
1   target defect is reproduced
125 revision is untestable for a non-defect reason
other abort: oracle/setup failure
```

The exact mapping may be wrapped by `scripts/bisect_oracle.py`; do not map every
command failure to bad.

## Ambiguous result

If commits B and C cannot build but A is good and D is bad, the result may be
`B..D`, not D. Improve historical environment or report the range.

## Merge-aware question

“Which integration commit brought the defect to main?” may require first-parent
history. “Which original change introduced it?” may require full ancestry. State
which question and path were searched.
