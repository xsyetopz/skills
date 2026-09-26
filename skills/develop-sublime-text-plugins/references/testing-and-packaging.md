# Testing and packaging

Cards for proving plugin behavior at the right level (pure logic, call
shapes, mutants, in-editor tests) and for shipping a package (static
checks, the `.sublime-package` archive, Package Control). Everything
offline runs through `sh assets/examples/verify.sh`.

Verification tier: **Executed** on macOS 27.0 arm64 with CPython 3.14.7
and CPython 3.8.20 via uv 0.12.15: pure tests, stub tests, 11 mutants,
3.8 compilation, the package checker, and archive build and listing.
**Not runnable here**: UnitTesting inside Sublime Text (the headless
Docker runner failed on this arm64 machine; error in its card), its
GitHub Actions, syntax tests, safe mode, ChannelRepositoryTools, and
publishing.

## Contents

- Pure-core unittest
- Call-shape stub of the host modules
- Mutant matrix
- UnitTesting host tests
- UnitTesting headless container runner
- UnitTesting in GitHub Actions
- Syntax test files
- Safe mode test session
- Package checker
- sublime-package archive and loose overrides
- Package Control channel entry
- ChannelRepositoryTools before a pull request

## Pure-core unittest

**Definition.** Standard-library `unittest` cases that import only
`core.py` and run under any CPython, one per decision (parsing, edit
order, freshness, operators, escaping, validation).

**Use when.**

- Every branch of logic that does not need the editor.
- Checking both host generations: run the same file under 3.8 and 3.14.

**Do not use when.**

- Claiming editor behavior from it (undo, drawing, key dispatch).

**Example.**

```python
import unittest

from harness import load

core, _plugin = load()


class EditPlanningTest(unittest.TestCase):
    def test_plan_is_last_to_first_normalized_and_non_empty(self):
        plan = core.plan_edits([(0, 3), (9, 6), (4, 4), (6, 9)])
        self.assertEqual(plan, [(6, 9), (0, 3)])


if __name__ == "__main__":
    unittest.main()
```

Runnable: `assets/examples/offline/test_core.py` (18 tests).

**Cost removed.** Editor round trips for logic bugs. Metric: `Ran 18
tests ... OK` on both interpreters.

**Verify.**

1. `sh assets/examples/verify.sh offline` and `... py38` print
   `test_core.py: Ran 18 tests ..., OK`.
1. `grep -c "import sublime" assets/examples/TodoLens/core.py` prints
   `0`: the tests need no host.

## Call-shape stub of the host modules

**Definition.** `offline/host_stub/sublime.py` and `sublime_plugin.py`
are typed stand-ins written from the API reference signatures;
`harness.py` installs them as `sys.modules["sublime"]` and
`["sublime_plugin"]` before importing `TodoLens.plugin`. They record
calls, queue `set_timeout`/`set_timeout_async` callbacks until a test
drains them, keep a text buffer and change count, and invalidate an
`Edit` after `run`. They prove the plugin's call names, arguments, order,
and decisions; they do not prove what Sublime Text does.

**Use when.**

- Testing adapter code paths: lifecycle, thread hand-off, freshness,
  command guards, context answers.

**Do not use when.**

- Asserting host behavior the stub does not model (drawing, undo
  grouping, whether `run_command` checks `is_enabled`): it leaves those
  out deliberately.
- Putting the stub on the plugin's import path inside the package: it
  must never ship or shadow the real modules.

**Example.**

```python
class AsyncTest(AdapterCase):
    def test_edit_during_scan_discards_result(self):
        self.type_text("TODO a")
        sublime.run_async()  # computed from change_count 1
        self.view.user_types("\nFIXME")  # count 2
        sublime.run_main()
        self.assertEqual(self.view.get_regions("todo_lens"), [])
```

Runnable: `assets/examples/offline/test_adapter.py` (23 tests).

**Cost removed.** Untested adapter code between pure logic and the
editor. Metric: `Ran 23 tests ... OK`.

**Verify.**

1. `sh assets/examples/verify.sh offline` prints
   `test_adapter.py: Ran 23 tests ..., OK`.
1. Every card that relies on the stub also names a host check marked
   Not runnable here.

## Mutant matrix

**Definition.** `offline/variants.py` maps a mutant name to a function
that swaps one core or plugin function for a defective copy;
`run_mutants.py` runs both suites once with `VARIANT` unset (must pass)
and once per mutant (the named test must fail).

**Use when.**

- Adding a test for a defect: add the mutant that reintroduces the
  defect and confirm the test kills it.

**Do not use when.**

- Counting a mutant as killed because an unrelated test fails: the
  runner requires the expected test name in the failure headers.

**Example.**

```python
def no_change_count(core, plugin):
    def is_fresh(snapshot, *, valid, change_count, current):
        return valid and current

    core.is_fresh = is_fresh
```

Recorded (both interpreters):

```text
reference: 41 tests passed
killed forward-order          2 failing, incl. test_mark_done_changes_...
killed no-change-count        2 failing, incl. test_edit_during_scan_...
...
11/11 mutants killed
```

**Cost removed.** Tests that pass whatever the code does. Metric: killed
mutants / total, 11/11.

**Verify.**

1. `sh assets/examples/verify.sh mutants` exits 0: the reference passes
   all 41 tests.
1. The same run prints `11/11 mutants killed`; a surviving mutant prints
   `SURVIVED <name>` and exits 1.

## UnitTesting host tests

**Definition.** [UnitTesting][ut] runs `unittest` cases inside Sublime
Text. It discovers `tests_dir` (default `tests`) with `pattern` (default
`test*.py`), both settable in `unittesting.json` at the package root, and
runs from the console with `window.run_command("unit_testing",
{"package": "Name"})`. `DeferrableTestCase` test methods may `yield` a
callable (wait until its result is met, default timeout 4000 ms), an
integer (wait that many ms), or `AWAIT_WORKER`.

**Use when.**

- Claiming editor behavior: undo steps, read-only views, selection
  results, regions published after the debounce.

**Do not use when.**

- Naming host tests `test_*.py` in a repository whose CI also runs
  `test_*.py` with plain Python: they cannot import `sublime` there.
  TodoLens uses `"pattern": "host_*.py"`.
- Sleeping instead of yielding a condition.
- Omitting `tests/__init__.py`: stdlib discovery then stops with
  `ImportError: Start directory is not importable` (recorded here with
  `TestLoader().discover("TodoLens/tests", pattern="host_*.py",
  top_level_dir="TodoLens")`); the README's layout shows the file.

**Example.**

```json
{
  "tests_dir": "tests",
  "pattern": "host_*.py",
  "deferred": true,
  "reload_package_on_testing": true
}
```

```python
def test_annotations_appear_after_debounce(self):
    self.prepare("a TODO: b", [(0, 0)])
    view = self.view
    yield lambda: bool(view.get_regions("todo_lens")) or None
    self.assertEqual(view.get_regions("todo_lens"),
                     [sublime.Region(2, 6)])
```

The README says the runner resumes when the callable's result "is not
`None`" but its own example waits on a boolean; `True or None` satisfies
both readings. Runnable in the editor: `TodoLens/tests/host_commands.py`
(6 tests).

**Cost removed.** Shipping behavior that only stubs have seen. Metric
(host, Not runnable here): UnitTesting's result line for 6 tests.

**Verify.**

1. Host (Not runnable here): install UnitTesting via Package Control,
   copy `TodoLens/` into `Packages/`, run the console command above; all
   6 pass. Repeat after saving `plugin.py` (reload).
1. Offline: `sh assets/examples/verify.sh py38` compiles the host test
   file under 3.8.

## UnitTesting headless container runner

**Definition.** UnitTesting's `docker/ut-run-tests PACKAGE_ROOT`
(`docker/run_tests.py`) builds a local image, installs Sublime Text and
UnitTesting in a container under Xvfb, runs the package's tests, and
streams results to stdout; `--file`, `--pattern`, `--tests-dir`,
`--failfast`, `--coverage`, `--dry-run`, and cache-volume options are
documented, and "test runs no longer commandeer your active editor
window" ([UnitTesting README][ut]).

**Use when.**

- Host tests must run from a terminal or an agent without touching the
  user's editor.

**Do not use when.**

- The host is arm64 without working amd64 emulation: the install script
  (`sbin/install_sublime_text.sh`, commit `1e968c5`, 7 Jun 2026) accepts
  only `x64` for Sublime Text 4. Recorded on this machine (macOS 27.0
  arm64, Docker 29.4.0, `DOCKER_DEFAULT_PLATFORM=linux/amd64`): the image
  built and `sublime_text_build_4215_x64.tar.xz` downloaded, then
  extraction failed 98 times with `tar: sublime_text/Packages: Cannot
  mkdir: Function not implemented`, exit status 2.
- Leaving the image and volume behind on a shared machine: pass
  `--docker-image` and `--cache-volume` names you remove afterwards.

**Example.**

```sh
git clone --depth 1 https://github.com/SublimeText/UnitTesting.git ut
cd TodoLens
python3 ../ut/docker/run_tests.py . --docker-image ut-todolens \
  --cache-volume ut-todolens-cache
docker rmi ut-todolens; docker volume rm ut-todolens-cache
```

**Cost removed.** Closing or disturbing the user's editor to run host
tests. Metric: UnitTesting's summary line in the terminal (6 tests for
TodoLens); not obtained here because of the error above.

**Verify.**

1. On an x86-64 Linux or macOS host with Docker: the command prints the
   6 TodoLens host tests as passing.
1. `docker images ut-todolens -q` prints nothing after cleanup.

## UnitTesting in GitHub Actions

**Definition.** UnitTesting publishes actions on branch `v1`:
`SublimeText/UnitTesting/actions/setup@v1` (must be first after
checkout), `run-tests@v1`, `run-syntax-tests@v1`, and
`run-color-scheme-tests@v1` ([UnitTesting README][ut]).

**Use when.**

- The package repository has CI and host tests; run a matrix over
  operating systems and `sublime-text-version: 4`.

**Do not use when.**

- The repository has no CI: do not add one unasked.

**Example.**

```yaml
name: ci-unit-tests
on: [push, pull_request]
jobs:
  run-tests:
    strategy:
      fail-fast: false
      matrix:
        os: ["ubuntu-latest", "macOS-latest", "windows-latest"]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: SublimeText/UnitTesting/actions/setup@v1
        with:
          sublime-text-version: 4
      - uses: SublimeText/UnitTesting/actions/run-tests@v1
```

**Cost removed.** Host tests that never run. Metric (CI, Not runnable
here): the job's test count per OS.

**Verify.**

1. Parse the YAML (`python -c 'import yaml,sys;
   yaml.safe_load(open(sys.argv[1]))' ci.yml`).
1. CI (Not runnable here): push to a branch and read the job log.

## Syntax test files

**Definition.** A syntax test is a file named `syntax_test_*` inside
`Packages/`, whose first line is `<comment> SYNTAX TEST "<syntax file>"`;
lines starting with the comment token then `^` test the scope at the
same column of the previous non-test line, `<-` at the comment column,
and `@` a symbol type; running the build command with the file selected
runs all syntax tests ([syntax tests][syntax]). The UnitTesting action
`run-syntax-tests@v1` runs them in CI ([UnitTesting README][ut]).

**Use when.**

- The package ships a `.sublime-syntax` file: give every scope change a
  test line.

**Do not use when.**

- Checking only that the YAML parses: parsing cannot show whether a
  scope stack is right.

**Example.** From the Sublime Text documentation:

```c
// SYNTAX TEST "Packages/C/C.sublime-syntax"
#pragma once
// <- source.c meta.preprocessor.c++
 // <- keyword.control.import
"Hello, World! // not a comment";
// ^ string.quoted.double
//                  ^ string.quoted.double - comment
```

**Cost removed.** Scope regressions that show only as wrong colors.
Metric (host, Not runnable here): failing assertions in the build output
panel, 0.

**Verify.**

1. Host (Not runnable here): open the `syntax_test_*` file and run
   Build; the output panel reports the assertion count and 0 failures.
1. CI (Not runnable here):
   `SublimeText/UnitTesting/actions/run-syntax-tests@v1` passes.

## Safe mode test session

**Definition.** `subl --safe-mode` starts Sublime Text with an alternate
data directory that "is fully erased when starting", only if the
application is fully closed; on Windows and macOS holding Shift+Alt or
Option at startup does the same ([safe mode][safe]). Data directories:
`~/Library/Application Support/Sublime Text (Safe Mode)/` (macOS),
`~/.config/sublime-text-safe-mode/` (Linux),
`%AppData%\Sublime Text (Safe Mode)\` (Windows).

**Use when.**

- Manual host checks need a clean profile without the user's packages.

**Do not use when.**

- The user's editor is open: safe mode will not start; do not close
  their session to get it.
- Keeping anything there: it is erased on the next start. Install
  UnitTesting and the package after starting.

**Example.**

```sh
subl --safe-mode
# then install UnitTesting (the README installs it via Package Control)
# and copy TodoLens/ into the safe-mode data directory's Packages/
```

**Cost removed.** Results influenced by the user's other packages and
settings. Metric (host, Not runnable here): the console shows only
Default, UnitTesting, and TodoLens loading.

**Verify.**

1. Host (Not runnable here): `subl --help` lists `--safe-mode: Launch
   using a sandboxed (clean) environment` ([command line][cli]).
1. Host (Not runnable here): after starting, the safe-mode data
   directory above exists and its `Packages/` holds only what you copied
   in.

## Package checker

**Definition.** `scripts/check_package.py PACKAGE [--external CMD]` runs
static checks with no editor: `.python-version` value, package name
without `.`, resource files parse (comments and trailing commas allowed),
every `"command"` resolves to a command class or `--external`, class
names without consecutive capitals, `input()` commands listed in
`.sublime-commands`, no import-time `sublime.*()` beyond the safe list,
no `__pycache__`, `.pyc`, `package-metadata.json` ([submitting][submit]),
or root `__init__.py` ("ST packages don't need and should not contain a
top-level `__init__.py`", [UnitTesting README][ut]).

**Use when.**

- Before every archive build or release, and after renaming commands.

**Do not use when.**

- Treating 0 issues as a host test: it reads files only.

**Example.**

```text
$ python scripts/check_package.py assets/examples/TodoLens \
    --external edit_settings
0 issue(s) in TodoLens
$ python scripts/check_package.py assets/examples/TodoLens
Default.sublime-commands: command 'edit_settings' is not defined
1 issue(s) in TodoLens
```

Recorded: it also caught `__pycache__` that `py_compile` wrote into the
package (5 issues); `verify.sh` now compiles a separate copy.

**Cost removed.** Broken palette, menu, and key entries, and generated
files in releases. Metric: issue count, 0.

**Verify.**

1. `python scripts/test_check_package.py` (4 tests) passes; its fixture
   produces 10 issues covering every rule.
1. `sh assets/examples/verify.sh check` prints `0 issue(s) in TodoLens`.

## sublime-package archive and loose overrides

**Definition.** A `.sublime-package` is a zip file with a different
extension; zipped packages live in `<data_path>/Installed Packages/`,
loose ones in `<data_path>/Packages/`, and "any loose files in the
package directory will override files stored in the .sublime-package
file" ([packages]). Members sit at the archive root. `.pyc` files and
`package-metadata.json` do not belong in a package; a
`.no-sublime-package` file keeps Package Control from installing it
packed ([submitting][submit]).

**Use when.**

- Testing the packed install, or distributing manually.

**Do not use when.**

- Testing the archive while a loose `Packages/<Name>/` copy exists: the
  loose files win, so the test runs the development copy.
- Zipping the parent directory: an extra `TodoLens/` level breaks
  resource names.

Note: the packages page says to create a new package "under
`<data_path>/Installed Packages/`" but opens it with "Browse Packages",
which is `Packages/`; the Locations section says loose packages live in
`Packages/`. Follow the Locations section.

**Example.** From `verify.sh package` (recorded):

```text
File Name                                             Modified             Size
.python-version                                2026-09-25 19:43:24            4
core.py                                        2026-09-25 19:43:24         7746
plugin.py                                      2026-09-25 19:43:24         9758
Context.sublime-menu                           2026-09-25 19:43:24          178
Default.sublime-commands                       2026-09-25 19:43:24          516
Default.sublime-keymap                         2026-09-25 19:43:24          328
TodoLens.sublime-settings                      2026-09-25 19:43:24          290
archive: 7 root-level members, no directories or .pyc
```

built with

```sh
cd TodoLens && python3 -m zipfile -c ../TodoLens.sublime-package \
  .python-version core.py plugin.py Context.sublime-menu \
  Default.sublime-commands Default.sublime-keymap \
  TodoLens.sublime-settings
```

**Cost removed.** Archives that load in development but not when
installed.
Metric: root-level members only, 0 `.pyc`.

**Verify.**

1. `sh assets/examples/verify.sh package` exits 0.
1. Host (Not runnable here): copy the archive to `Installed Packages/`,
   remove any loose `Packages/TodoLens/`, restart, run "TodoLens: List
   Markers".

## Package Control channel entry

**Definition.** For GitHub or Bitbucket hosting, the package root is the
repository root, releases come from tags that are semantic versions, and
the entry goes into the proper JSON file in the channel's `repository/`
folder; branch-based releases are deprecated and not accepted for new
packages; `version`, `url`, and `date` sub-fields are not allowed in the
default channel ([submitting][submit]). Each release needs a
`"sublime_text"` selector (`*`, `<N`, `<=N`, `>N`, `>=N`, `N - M`);
`"tags"` may be a prefix string; `"platforms"` and `"python_versions"`
(valid values "3.3" and "3.8") are optional ([example repository][repo]).

**Use when.**

- Publishing a new package or a new release line.

**Do not use when.**

- Submitting before searching for an existing package that does the job:
  Package Control asks authors to improve that one first.
- Using `"sublime_text": "*"` for a package that needs the 3.8 host or
  4050+ APIs: builds before 4050 would run it on 3.3.
- Opening the pull request without the user's authorization.

**Example.**

```json
{
  "name": "TodoLens",
  "details": "https://github.com/example/TodoLens",
  "releases": [
    {
      "sublime_text": ">=4050",
      "tags": true
    }
  ]
}
```

**Cost removed.** Installs on builds that cannot load the package.
Metric: the selector's lower bound equals the highest minimum build of
any API used (here 4050: annotations and the 3.8 host).

**Verify.**

1. `python -c 'import json,sys; json.load(open(sys.argv[1]))' entry.json`
   parses the entry.
1. ChannelRepositoryTools (next card) passes.

## ChannelRepositoryTools before a pull request

**Definition.** Package Control's submission steps: fork and clone the
channel, add the entry, install ChannelRepositoryTools, run
"ChannelRepositoryTools: Test Default Channel" from the palette, then
open a pull request ([submitting][submit]).

**Use when.**

- After editing a channel `repository/*.json` file.

**Do not use when.**

- Substituting a JSON parse for it: the tool checks channel rules the
  parse does not.

**Example.**

```text
Command Palette > ChannelRepositoryTools: Test Default Channel
```

**Cost removed.** Review rounds for entries that break channel rules.
Metric (host, Not runnable here): the tool's failure count, 0.

**Verify.**

1. Before: `python -c 'import json,sys; json.load(open(sys.argv[1]))'
   repository/t.json` (the edited file) parses.
1. Host (Not runnable here): run the command with the fork open and read
   its output panel; failures are 0.

[ut]: https://github.com/SublimeText/UnitTesting
[safe]: https://www.sublimetext.com/docs/safe_mode.html
[packages]: https://www.sublimetext.com/docs/packages.html
[submit]: https://packagecontrol.io/docs/submitting_a_package
[repo]: https://raw.githubusercontent.com/wbond/package_control/master/example-repository.json
[cli]: https://www.sublimetext.com/docs/command_line.html
[syntax]: https://www.sublimetext.com/docs/syntax.html#testing
