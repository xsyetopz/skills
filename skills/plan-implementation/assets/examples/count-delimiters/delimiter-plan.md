# Plan: count delimiters without building a list

Goal: `count_delimiters` returns the same results and raises the same
errors as the current `len(text.split(delimiter)) - 1`, with less peak
memory on large inputs. Requirement source: issue 318.

Out of scope: changing the delimiter definition (it stays a substring of
the input `str`), other callers of `split`.

## Tasks

- T1 [depends: -] [files: tests/test_counter.py] [estimate: 1h] Add
  boundary tests that pin the current behavior, including the empty
  delimiter.
  Verify: `python3 -m unittest tests.test_counter`
  Done when: all cases pass against the split-based implementation.
- T2 [depends: T1] [files: counter.py] [estimate: 1h] Replace the body
  with `str.count` behind an empty-delimiter guard, keeping the old
  function as the test oracle.
  Verify: `python3 -m unittest tests.test_counter`
  Done when: every case still passes, including the ValueError case.
- T3 [depends: T2] [files: bench.py] [estimate: 1h] Compare peak traced
  memory for one call on 1 MB of text.
  Verify: `python3 bench.py`
  Done when: the count version's peak is below the split version's.

## Risks

- If a caller passes an empty delimiter, then `str.count` would return
  `len(text) + 1` instead of raising; T1 pins the ValueError and T2 keeps
  the guard.

## Rollback

Revert the T2 commit; T1's tests stay valid for the old code.
