# Review: apply config edits

Findings on `config-plan.md`, most severe first. Each finding names the
step, the violated constraint, a concrete counterexample, the smallest
correction, and the check that proves it.

## F1 blocker: T1 loses concurrent edits

- Step: T1 "Read `settings.json`, merge the edits, and write the file
  back."
- Constraint violated: "Another tool may edit the same file at the same
  time" (goal).
- Counterexample: read version A; the other tool writes B with `font`;
  T1 writes A plus the edits; `font` is gone.
  `tests/test_config_store.py::test_lost_update` reproduces it.
- Correction: detect a change between read and publication and re-read
  (`versioned_update` raises `StaleWriteError`).
- Verify: `python3 -m unittest tests.test_config_store`.

## F2 blocker: T1 can destroy the file on bad input

- Step: T1 writes with `open(path, "w")` before serialization finishes.
- Constraint violated: "malformed input must leave the file unchanged".
- Counterexample: an unserializable value truncates the file to 0 bytes
  (`test_unserializable_edit_destroys_file`).
- Correction: serialize fully, write a temporary file, then `os.replace`.
- Verify: `test_unserializable_edit_leaves_file`.

## F3 major: "Retry on any failure" can re-apply or overwrite

- Step: T1 "Retry on any failure."
- Problem: retrying after F1's stale-write error without re-reading
  repeats the lost update; retrying on `TypeError` never succeeds.
- Correction: retry only `StaleWriteError`, re-reading each time, with a
  bounded count; fail fast on validation errors.

## F4 major: T2's claims do not match the repository

- `src/config_cli.py` does not exist and the task does not say to create
  it; `just test-config` is not a recipe (no justfile).
  `audit_plan_claims.py` reports both as MISSING.
- Correction: name the real CLI module or mark the file as new; use an
  existing verify command.

## F5 minor: done conditions are not observable

- "Edits appear in the file" and "the CLI works" do not cover the
  concurrency and bad-input constraints; add the four tests above as the
  done conditions.
