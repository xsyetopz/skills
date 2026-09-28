# How we write plans

A plan is a Markdown file with a goal, an out-of-scope line, and a task
list. Each task is one list item in execution order:

```text
- T3 [depends: T1, T2] [files: app/x.py, tests/test_x.py] One-line summary.
  Verify: `python3 -m unittest tests.test_x`
  Done when: <observable condition>.
```

`[depends: -]` marks a task with no prerequisites. Every task needs
`[files: ...]`, a `Verify:` line with one backticked command that exists in
this repository, and a `Done when:` line.
