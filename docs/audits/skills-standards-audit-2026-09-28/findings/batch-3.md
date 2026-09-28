# Batch 3 findings

Skills: develop-eclipse-ide-plugins, develop-intellij-platform-plugins,
develop-neovim-plugins, develop-sublime-text-plugins,
develop-vscode-extensions, develop-zed-editor-extensions,
create-agent-hooks.

## develop-eclipse-ide-plugins

No findings.

## develop-intellij-platform-plugins

- [FL-01] **fix** SKILL.md:32: the workflow step reads
  `python3 <skill>/scripts/check_plugin_xml.py --src-root ...`. Every
  other command and every other skill in this batch gives a path
  relative to the skill root (`scripts/check_plugin_xml.py`); `<skill>`
  is an unresolved placeholder, not a real path segment, so a literal
  copy-paste of the command fails. Fix: drop `<skill>/` so the command
  reads `python3 scripts/check_plugin_xml.py --src-root ...`.

## develop-neovim-plugins

No findings.

## develop-sublime-text-plugins

No findings.

## develop-vscode-extensions

No findings.

## develop-zed-editor-extensions

No findings.

## create-agent-hooks

- [SC-02] **fix** assets/handlers/guard_shell.py, stop_gate.py,
  session_context.py `--help`: none of the three include an "Exit
  status" section or "Examples", unlike every `scripts/*.py --help` in
  this skill and in the other six skills in this batch (for example
  `scripts/check_hook_config.py --help` has both). These handlers are
  bundled tools referenced from SKILL.md's "Bundled tools" list, so the
  same expectation applies. Fix: add the exit-status and example blocks
  used by the `scripts/*.py --help` texts in the same skill.
- [SC-03] **consider** scripts/check_hook_config.py: on a missing file
  the error is `error: [Errno 2] No such file or directory:
  '/no/such.json'`, with no "expected" or "try" guidance, unlike
  `scripts/merge_hooks.py`'s `--handler is not valid JSON: ...` or the
  richer messages in the other skills' checkers (for example
  `develop-vscode-extensions/scripts/check_manifest.py`: "expected a
  readable package.json holding a JSON object"). Fix: append what the
  argument should be, e.g. "; pass an existing hook configuration file".
- [SC-03] **consider** scripts/merge_hooks.py: when the target file's
  parent directory cannot be created (permission denied on the parent),
  the script raises an unhandled `OSError` traceback instead of a
  one-line error, unlike its own handled cases (unreadable file, bad
  `--handler` JSON). This is a narrow case (a non-writable parent), not
  the everyday "bad argument" path, so it is a judgment call whether it
  is worth a catch. Fix: wrap the `mkdir`/write in a try/except that
  reports the path and reason, matching the rest of the script's error
  style.

## Batch patterns

1. All seven skills follow the same shape closely (routing table with
   Use-when/Do-not-use-when references, a Rules section carrying the
   gotchas, a Bundled tools section, Completion evidence, and
   evals with a 10/10 near-miss-heavy trigger split), so most findings
   are narrow misses rather than structural gaps — this batch is close
   to conformant overall.
1. The one real defect (the `<skill>/` placeholder in
   develop-intellij-platform-plugins) is the kind of thing that only
   shows up by literally trying to run every quoted command; the other
   six skills' equivalent commands were all copy-paste-correct.
1. `scripts/*.py --help` texts are consistently strong (usage, exit
   codes with meanings, output format, examples) across all seven
   skills; the only shortfall found was in create-agent-hooks's
   `assets/handlers/*.py`, which sit outside the `scripts/` directory
   the mechanical checker and the repo's own convention cover, so they
   quietly missed the same bar.
