# Plan under review: apply config edits

Goal: apply a user's key/value edits to `settings.json`. Another tool may
edit the same file at the same time; malformed input must leave the file
unchanged.

- T1 [depends: -] [files: config_store.py] Read `settings.json`, merge
  the edits, and write the file back. Retry on any failure.
  Verify: `python3 -m unittest tests.test_config_store`
  Done when: edits appear in the file.
- T2 [depends: T1] [files: src/config_cli.py] Expose the command.
  Verify: `just test-config`
  Done when: the CLI works.
