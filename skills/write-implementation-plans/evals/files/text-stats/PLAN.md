# Plan: word counts

Goal: the report shows the number of words in a text.

- T1 [depends: -] [files: text_stats.py, tests/test_text_stats.py] Add
  `word_count(text)`, which counts runs of non-whitespace characters, with
  tests for an empty string, repeated spaces, and tabs and newlines.
  Verify: `python3 -m unittest discover -s tests -t .`
  Done when: the new tests pass and `word_count("  a\tb\nc ")` returns 3.
