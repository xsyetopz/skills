# Languages, grammars, and queries

Cards for adding a language: `config.toml`, the Tree-sitter grammar, and
each query file Zed reads. The runnable fixture is
[`assets/examples/makefile/`][fixture], a GNU Make language on
[tree-sitter-make][grammar] pinned at v1.1.1
(`5e9e8f8ff3387b0edcaa90f46ddf3629f4cfeb1d`). `verify.sh` compiled and
ran every query against [`samples/Makefile`][sample] with the
tree-sitter CLI 0.27.0 (Executed), and `check_queries.py` checked every
node, field, and capture name against the grammar's `node-types.json`
(Executed). Capture rules come from Zed v1.21.0's
[`grammar.rs`][grammar-rs] and the [languages docs][lang-docs].

## Contents

- [Language directory and config.toml](#language-directory-and-configtoml)
- [File matching](#file-matching)
- [Grammar with a pinned revision](#grammar-with-a-pinned-revision)
- [Local grammar during development](#local-grammar-during-development)
- [highlights.scm](#highlightsscm)
- [Fallback highlight captures](#fallback-highlight-captures)
- [brackets.scm](#bracketsscm)
- [outline.scm](#outlinescm)
- [indents.scm](#indentsscm)
- [injections.scm](#injectionsscm)
- [overrides.scm and scoped settings](#overridesscm-and-scoped-settings)
- [textobjects.scm](#textobjectsscm)
- [redactions.scm](#redactionsscm)
- [runnables.scm and tasks.json](#runnablesscm-and-tasksjson)
- [Query check](#query-check)

## Language directory and config.toml

**Definition.** Each language is a directory under `languages/` with a
`config.toml`. `name` is the display name and the exact string
`language_servers.*.languages` must use; `grammar` is a key of
`[grammars]`. Optional keys include `line_comments`, `block_comment`,
`tab_size` (1–128), `hard_tabs`, `brackets` (each entry needs `start`,
`end`, `close`, and `newline`), `autoclose_before`, `word_characters`,
and `overrides` ([LanguageConfig][config-rs]). Besides `config.toml`,
the packager accepts only the known query files,
`semantic_token_rules.json`, `tasks.json`, and declared snippet files;
any other file fails packaging ([CLI][cli-rs]).

**Use when.**

- The extension adds a language Zed does not ship. The registry requires
  every language to use a grammar declared in its own `extension.toml`
  ([FAQ][faq]).

**Do not use when.**

- Adding only a language server for an existing language. Declare the
  server and target the existing `name`, as `marksman-lsp` does for
  `Markdown`.
- The name collides with a built-in, such as `Shell Script` (Zed's Bash)
  or `Markdown`. Lookups go by name, so which definition a file gets is
  unclear (inferred from the name-keyed registry, not observed). Pick
  a distinct name.
- Putting sample or test inputs in the language directory. The packager
  rejects them as "not a supported file in a language directory"; keep
  them elsewhere, such as the fixture's `samples/`.

**Example.** Runnable: `languages/makefile/config.toml`.

```toml
name = "Makefile"
grammar = "make"
path_suffixes = ["mk", "mak", "Makefile", "makefile", "GNUmakefile"]
first_line_pattern = '^#!.*\bmake\b'
line_comments = ["# "]
hard_tabs = true
tab_size = 8
autoclose_before = ")}"
brackets = [
  { start = "(", end = ")", close = true, newline = false },
  { start = "{", end = "}", close = true, newline = false },
  { start = "\"", end = "\"", close = true, newline = false, not_in = [
    "comment",
    "string",
  ] },
]

[overrides.comment]
completion_query_characters = ["-"]
```

`hard_tabs = true` matters here because GNU Make recipe lines must start
with a tab.

**Cost removed.** A language directory that fails packaging.
`check_extension.py` counts missing `name` or `grammar`, undeclared
grammars, incomplete bracket pairs, and stray files; it printed
`0 errors` on the fixture (Executed).

**Verify.**

1. `python3 scripts/check_extension.py --registry
   assets/examples/makefile` prints `0 errors, 0 warnings`. Executed.
1. In Zed, the language picker lists "Makefile" (Not runnable here).

## File matching

**Definition.** Zed tests each `path_suffixes` entry against a file's
extension, file name, and full path. An entry matches when the candidate
equals it or ends with `.<entry>`, which is why `Makefile` matches the
file name `Makefile` ([available_languages.rs][match-rs]). Entries are
literal strings, not globs. `first_line_pattern` is a regular expression
tested against the first line, for files without a telling name
([languages docs][lang-docs]).

**Use when.**

- `path_suffixes`: extensions and fixed file names (`mk`, `Makefile`).
- `first_line_pattern`: shebang or modeline files, such as
  `#!/usr/bin/make -f`.

**Do not use when.**

- Globs such as `*.mk` never match. `check_extension.py` reports
  `path_suffixes are literal, not globs`.
- A broad regular expression such as `make` captures unrelated files
  whose first line contains the word.

**Example.**

```toml
path_suffixes = ["mk", "mak", "Makefile", "makefile", "GNUmakefile"]
first_line_pattern = '^#!.*\bmake\b'
```

**Cost removed.** Files that open as Plain Text. The checker flags globs
and warns when a pattern does not compile with Python's `re` (unit test
`test_uncompilable_first_line_pattern_warns`, Executed). Zed uses Rust's
`regex` crate, so that warning is a prompt to check the pattern, not a
verdict.

**Verify.**

1. `python3 -c "import re; print(bool(re.search(r'^#!.*\bmake\b',
   '#!/usr/bin/make -f')))"` prints `True`. Executed.
1. In Zed, `Makefile`, `rules.mk`, and a `#!/usr/bin/make -f` script
   all show "Makefile" (Not runnable here).

## Grammar with a pinned revision

**Definition.** `[grammars.<name>]` in `extension.toml` with
`repository`, `rev` (alias `commit`), and optional `path` for a grammar
in a subdirectory ([manifest source][manifest-rs]). Zed fetches `rev` at
depth 1, compiles `src/parser.c` (plus `src/scanner.c` if present) with
wasi-sdk clang, and exports `tree_sitter_<name>`
([builder source][builder-rs]). So `<name>` must equal the suffix of the
parser's C function: tree-sitter-make's `src/parser.c` defines
`tree_sitter_make`, so the key is `make`. A mismatched key fails to
export the symbol (inferred from the link flags, not executed).

**Use when.**

- Every language the extension defines.
- Updating the grammar. Change `rev` and re-run the query check in the
  same change; node names can change between revisions.

**Do not use when.**

- `rev` is a branch or tag name. A branch moves, so a later build can
  compile a different grammar against the same queries.
  `check_extension.py` requires a 40-character SHA; that is this
  skill's policy, while the docs only say "such as the SHA of a Git
  commit".
- Reusing a built-in or another extension's grammar. The registry FAQ
  forbids it ([FAQ][faq]).

**Example.**

```toml
[grammars.make]
repository = "https://github.com/tree-sitter-grammars/tree-sitter-make"
rev = "5e9e8f8ff3387b0edcaa90f46ddf3629f4cfeb1d"
```

Find the SHA for a tag and the exported function:

```sh
gh api repos/tree-sitter-grammars/tree-sitter-make/tags \
  --jq '.[0] | .name + " " + .commit.sha'
rg -o 'tree_sitter_[a-z_]+\(void\)' src/parser.c
```

```text
v1.1.1 5e9e8f8ff3387b0edcaa90f46ddf3629f4cfeb1d
tree_sitter_make(void)
```

**Cost removed.** Queries broken by grammar drift. The verify script's
mutant `rev = "main"` is rejected with `pin a
40-character commit SHA` (Executed).

**Verify.**

1. `sh assets/examples/verify.sh` prints `ok   mutant rejected: grammar
   pinned to a branch`. Executed.
1. After `verify.sh fetch`, `git -C
   "$CACHE/tree-sitter-make-<sha>" rev-parse HEAD` prints
   `5e9e8f8ff3387b0edcaa90f46ddf3629f4cfeb1d`. Executed.

## Local grammar during development

**Definition.** A `repository` of `file:///abs/path/to/grammar` makes
Zed load the grammar from the local filesystem. `rev` must still name a
commit in that repository ([languages docs][lang-docs]).

**Use when.**

- Developing the grammar and queries together before pushing the
  grammar.

**Do not use when.**

- Publishing. Registry CI builds from a clean checkout where the path
  does not exist; `check_extension.py --registry` reports `file://
  grammars work only for dev installs`.

**Example.**

```toml
[grammars.make]
repository = "file:///Users/me/src/tree-sitter-make"
rev = "5e9e8f8ff3387b0edcaa90f46ddf3629f4cfeb1d"
```

**Cost removed.** A push to a remote for every grammar iteration. The
checker stops the local path before it reaches a registry PR.

**Verify.**

1. `check_extension.py EXT_DIR` (without `--registry`) accepts it;
   `--registry` rejects it. Unit test `test_file_url_grammar_is_dev_only`
   Executed.
1. A dev install loads the grammar (Not runnable here).

## highlights.scm

**Definition.** A Tree-sitter query whose capture names are theme syntax
keys such as `@comment`, `@keyword`, and `@function`. The docs list 43
supported captures ([languages docs][lang-docs]); themes can also style
dotted names such as `@function.builtin`. Captures starting with `_` are
private ([grammar.rs][grammar-rs]).

**Use when.**

- Every language. Without it there is no syntax coloring.

**Do not use when.**

- Copying another grammar's `highlights.scm`. Node names differ; the
  checker reports `no named node ...` for each foreign node.
- Relying on unchecked node names. tree-sitter-make has no `identifier`
  node, for example; targets are `(targets
  (word))`.

**Example.** Excerpt of `languages/makefile/highlights.scm`:

```scheme
(comment) @comment

(targets
  (word) @function)

(variable_assignment
  name: (word) @variable)

(automatic_variable) @variable.special

[
  "define"
  "endef"
  "ifeq"
  "endif"
] @keyword
```

Executed on `samples/Makefile`: 48 captures, including `comment` on line
1 and `variable` for `CC`, `CFLAGS`, and `SRC`.

**Cost removed.** Invalid patterns, which make Zed drop the whole query.
`check_queries.py` prints `0 errors` against `node-types.json`,
`tree-sitter query` compiles the file, and `@name` values outside the
documented list print `WARN`.

**Verify.**

1. `python3 scripts/check_queries.py languages/makefile --node-types
   .../src/node-types.json` prints `0 errors`. Executed.
1. `tree-sitter query -p <grammar> highlights.scm samples/Makefile`
   lists captures. Executed.

## Fallback highlight captures

**Definition.** Several captures on one node, such as `(node) @a @b`.
Zed resolves them right to left: it uses the rightmost capture the
active theme styles, then the next one left ([languages
docs][lang-docs]).

**Use when.**

- A specific key few themes define (`@function.builtin`) needs a common
  key (`@function`) as fallback.

**Do not use when.**

- The order is reversed (`@function.builtin @function`). The common key
  wins in every theme that defines it, so the specific key is never
  used.

**Example.**

```scheme
(function_call) @function @function.builtin
```

The fixture theme `ember-theme` defines `function.builtin`, so
`$(wildcard ...)` uses it; themes without that key fall back to
`function`.

**Cost removed.** Unstyled nodes in themes that lack the specific key:
one capture list serves both kinds of theme.

**Verify.**

1. `tree-sitter query` shows both captures on `$(wildcard *.c)`.
   Executed as part of the 48 captures.
1. In Zed, compare the color of `wildcard` under Ember Dark and under a
   theme without `function.builtin` (Not runnable here).

## brackets.scm

**Definition.** Patterns with the required captures `@open` and
`@close`. If either is missing, Zed logs an error and ignores the file
([grammar.rs][grammar-rs]). `(#set! rainbow.exclude)` and
`(#set! newline.only)` change behavior per pattern.

**Use when.**

- The language has paired delimiters. Zed uses them for matching,
  rainbow coloring, and highlighting the pair at the cursor.

**Do not use when.**

- Quote pairs would get rainbow colors. Exclude them.
- The delimiter is not a separate token in the grammar, so the pattern
  cannot match. Check with `tree-sitter query`.

**Example.** `languages/makefile/brackets.scm`:

```scheme
("(" @open ")" @close)
("{" @open "}" @close)
(("\"" @open "\"" @close) (#set! rainbow.exclude))
```

Executed: 16 captures on the sample (8 open/close pairs).

**Cost removed.** A brackets file Zed ignores silently. The checker
reports `missing required @open; Zed ignores the
file`.

**Verify.**

1. `check_queries.py` prints `0 errors`. Executed.
1. `tree-sitter query ... brackets.scm` prints open/close pairs.
   Executed.

## outline.scm

**Definition.** Patterns with the required captures `@item` (whole
range) and `@name` (label). Optional: `@context`, `@context.extra`,
`@open`, `@close`, and `@annotation` ([grammar.rs][grammar-rs]). Text
predicates such as `#not-match?` filter matches.

**Use when.**

- The language has named top-level constructs, such as Make rules,
  variables, and `define` blocks.

**Do not use when.**

- Capturing noise such as `.PHONY` special targets. Filter them with a
  predicate.
- Omitting `@name`. Zed drops the whole outline query.

**Example.** `languages/makefile/outline.scm`:

```scheme
((rule
  (targets) @name) @item
  (#not-match? @name "^\\."))

(variable_assignment
  name: (word) @name) @item

(define_directive
  "define" @context
  name: (word) @name) @item
```

Executed names on the sample: `CC`, `CFLAGS`, `SRC`, `greet` (context
`define`), `LD`, `all`, `build/app`, and `clean`. `.PHONY` is filtered
out.

**Cost removed.** Outline noise. Without the predicate, an earlier run in this
session listed `.PHONY` as a target.

**Verify.**

1. `tree-sitter query ... outline.scm samples/Makefile | grep name,`
   shows the names above. Executed.
1. The verify mutant `(target) @name` is rejected with ``no named node
   `target` ``. Executed.

## indents.scm

**Definition.** `@indent` (required) marks a node whose inner lines
indent; `@start` and `@end` narrow the range; `@outdent` ends the
innermost range; `@start.<name>` marks blocks for the config key
`decrease_indent_patterns` ([grammar.rs][grammar-rs], [languages
docs][lang-docs]).

**Use when.**

- The language has syntactic blocks with indented bodies.

**Do not use when.**

- Only line patterns matter. Use `increase_indent_pattern` and
  `decrease_indent_pattern` in `config.toml`.

**Example.** `languages/makefile/indents.scm`:

```scheme
(rule
  (recipe) @indent)

(define_directive
  "define" @start
  "endef" @end) @indent

(conditional
  "endif" @end) @indent
```

Executed: 7 captures, covering the `define ... endef` range, the
`ifeq ... endif` range, and the two recipes.

**Cost removed.** Manual indentation after Enter inside a recipe; the
new line starts with a tab because `hard_tabs = true`.

**Verify.**

1. `check_queries.py` prints `0 errors`. Executed.
1. In Zed, press Enter at the end of `all: build/app` and type a
   command: the line starts with a tab (Not runnable here).

## injections.scm

**Definition.** `@injection.content` (or `@content`) marks text another
language parses. The language comes from the text of
`@injection.language` (or `@language`), or from
`(#set! injection.language "name")`. `(#set! injection.combined)` parses
all matches as one document. Using both the short and long form of the
same capture is an error. Without content, Zed logs "missing required
capture" and ignores the file ([grammar.rs][grammar-rs]). The name is
looked up by language name or path suffix
(`language_for_name_or_extension` in [language_registry.rs][registry-rs]).

**Use when.**

- Embedded code, such as Make recipe lines (shell) or fenced code
  blocks.

**Do not use when.**

- The injected language is not available in Zed. The name resolves to
  nothing and the text stays plain.

**Example.** `languages/makefile/injections.scm`:

```scheme
((shell_text) @injection.content
  (#set! injection.language "bash"))
```

`bash` is a path suffix and the code-fence name of the built-in "Shell
Script" language. Executed: 3 captures (`mkdir -p $(@D)`, the compile
line, and `rm -rf build`).

**Cost removed.** Unhighlighted recipe text. The checker reports missing
content and conflicting capture forms before Zed logs them.

**Verify.**

1. `check_queries.py` prints `0 errors`. Executed.
1. In Zed, `mkdir` in a recipe gets Shell Script colors (Not runnable
   here).

## overrides.scm and scoped settings

**Definition.** Captures in `overrides.scm` name scopes such as
`@string` and `@comment`; a `.inclusive` suffix extends the range to its
ends. `config.toml` refers to scopes in `[overrides.<scope>]` and
`brackets[].not_in`. If `overrides.scm` exists and a referenced scope
has no capture, the language fails to load with "has overrides in
config not in query" ([grammar.rs][grammar-rs]). If the file does not
exist, the references do nothing (inferred: the source runs the check
only when the file exists).

**Use when.**

- Auto-closing should stop inside strings or comments.
- Completion or word characters differ inside a scope.

**Do not use when.**

- Referencing scopes without shipping `overrides.scm`. Zed's own Proto
  extension does this; `check_extension.py` warns:
  `not_in 'string' has no effect: no overrides.scm`.

**Example.** `languages/makefile/overrides.scm`:

```scheme
(comment) @comment.inclusive

(string) @string
```

It captures the scopes `languages/makefile/config.toml` references in
`not_in` and `[overrides.comment]`:

```toml
brackets = [
  { start = "(", end = ")", close = true, newline = false },
  { start = "{", end = "}", close = true, newline = false },
  { start = "\"", end = "\"", close = true, newline = false, not_in = [
    "comment",
    "string",
  ] },
]

[overrides.comment]
completion_query_characters = ["-"]
```

**Cost removed.** A language that fails to load. The checker makes the
missing scope an `ERROR` (unit test
`test_not_in_scope_must_exist_in_overrides`, Executed).

**Verify.**

1. `python3 scripts/test_check_extension.py` passes. Executed.
1. In Zed, typing `"` inside a comment does not insert a second `"`
   (Not runnable here).

## textobjects.scm

**Definition.** Captures `@function.inside`, `@function.around`,
`@class.inside`, `@class.around`, `@comment.inside`, and
`@comment.around`, which Vim mode uses for motions such as `]m` and text
objects such as `af` and `if`. Any other capture name only logs a
warning ([languages docs][lang-docs], [grammar.rs][grammar-rs]).

**Use when.**

- Vim-mode users need structural motions. A Make rule acts as a
  "function" whose recipe is the inside.

**Do not use when.**

- The mapping is forced, such as every variable as a class. Motions then
  jump somewhere unexpected.

**Example.** `languages/makefile/textobjects.scm`:

```scheme
(rule
  (recipe) @function.inside) @function.around

(comment)+ @comment.around
```

Executed: 5 captures (two rules with inside and around, plus the header
comment).

**Cost removed.** Missing structural selection in Vim mode: without the
file, `vaf` selects nothing in a Makefile.

**Verify.**

1. `tree-sitter query ... textobjects.scm` shows the ranges. Executed.
1. In Zed with Vim mode, `vaf` inside a recipe selects the rule (Not
   runnable here).

## redactions.scm

**Definition.** The required capture `@redact` marks text Zed hides
while you share your screen in a collaboration session ([languages
docs][lang-docs]).

**Use when.**

- The language holds values that can be secrets, such as Makefile
  variable values, `.env` files, or configuration files.

**Do not use when.**

- The capture covers code collaborators need to read, such as a whole
  rule. Redact only values.

**Example.** `languages/makefile/redactions.scm`:

```scheme
(variable_assignment
  value: (text) @redact)
```

Executed: 4 captures (`cc`, `-O2 -g`, `$(wildcard *.c)`, `$(CC)`).

**Cost removed.** Values exposed during screen sharing. Count the
redacted spans in `tree-sitter query` output.

**Verify.**

1. `check_queries.py` prints `0 errors`. Executed.
1. In a Zed screen share, the values render redacted (Not runnable
   here).

## runnables.scm and tasks.json

**Definition.** `@run` places a run button. Other captures not starting
with `_` become the task variables `ZED_CUSTOM_<capture>`.
`(#set! tag <tag>)` binds the match to task templates with the same tag.
Zed loads an extension language's `tasks.json` as that language's task
templates ([extension_host.rs][host-rs], [languages docs][lang-docs],
[tasks docs][tasks-docs]).

**Use when.**

- A syntax node maps to a command, such as a Make target to
  `make <target>`.

**Do not use when.**

- No task template carries the tag; the button has nothing to run.

**Example.** `languages/makefile/runnables.scm` and `tasks.json`:

```scheme
((rule
  (targets
    (word) @run @make_target))
  (#not-match? @make_target "^\\.")
  (#set! tag make-target))
```

```json
[
  {
    "label": "make $ZED_CUSTOM_make_target",
    "command": "make",
    "args": ["$ZED_CUSTOM_make_target"],
    "tags": ["make-target"]
  }
]
```

Executed: run buttons on `all`, `build/app`, and `clean`, with
`make_target` holding the same text.

**Cost removed.** Typing `make <target>` in a terminal: each target gets
a gutter button.

**Verify.**

1. `tree-sitter query ... runnables.scm` shows `run` and `make_target`
   on each target. Executed.
1. In Zed, the gutter button on `clean` runs `make clean` (Not runnable
   here).

## Query check

**Definition.** Two complementary checks. `check_queries.py` (standard
library only) checks balanced delimiters, per-file capture rules, and
node, field, and anonymous-token names against the pinned grammar's
`src/node-types.json`. `tree-sitter query -p <grammar> Q FILE` compiles
the query with the real parser and prints the matches. Zed's packager
does the equivalent compile (`Query::new`) for every query file
([CLI][cli-rs]).

**Use when.**

- Before every dev install and every grammar `rev` change.

**Do not use when.**

- Treating a clean `check_queries.py` run as proof that patterns match.
  It proves only that the names exist; run `tree-sitter query` on a real
  sample for matches.

**Example.**

```sh
sh assets/examples/verify.sh fetch     # clones the grammar at rev
TREE_SITTER=/path/to/tree-sitter sh assets/examples/verify.sh
```

```text
ok   makefile queries: 9 files, 0 errors, 0 warnings (with node types)
ok   mutant rejected: outline node missing from the pinned grammar
note SDKROOT=/Library/Developer/CommandLineTools/SDKs/MacOSX15.2.sdk
ok   tree-sitter 0.27.0: highlights.scm, 48 captures
```

The `SDKROOT` note is machine-specific: the default macOS 27 SDK here
fails to link the parser (`ld: tapi error: malformed file`), so the
script retries with each installed SDK.

**Cost removed.** Invalid queries reaching Zed or registry CI. On a
wrong node name the CLI exits 1 with
`Query error at 1:29. Invalid node type "identifier"` (Executed on a
scratch query).

**Verify.**

1. Both commands exit 0 on the fixture. Executed.
1. `python3 scripts/test_check_queries.py` passes 9 tests. Executed.

[fixture]: ../assets/examples/makefile/
[sample]: ../assets/examples/samples/Makefile
[grammar]: https://github.com/tree-sitter-grammars/tree-sitter-make
[lang-docs]: https://zed.dev/docs/extensions/languages
[tasks-docs]: https://zed.dev/docs/tasks
[faq]: https://zed.dev/docs/extensions/publishing/faq#grammar-reuse
[config-rs]: https://github.com/zed-industries/zed/blob/v1.21.0/crates/language_core/src/language_config.rs
[grammar-rs]: https://github.com/zed-industries/zed/blob/v1.21.0/crates/language_core/src/grammar.rs
[match-rs]: https://github.com/zed-industries/zed/blob/v1.21.0/crates/language/src/available_languages.rs
[registry-rs]: https://github.com/zed-industries/zed/blob/v1.21.0/crates/language/src/language_registry.rs
[manifest-rs]: https://github.com/zed-industries/zed/blob/v1.21.0/crates/extension/src/extension_manifest.rs
[builder-rs]: https://github.com/zed-industries/zed/blob/v1.21.0/crates/extension/src/extension_builder.rs
[cli-rs]: https://github.com/zed-industries/zed/blob/v1.21.0/crates/extension_cli/src/main.rs
[host-rs]: https://github.com/zed-industries/zed/blob/v1.21.0/crates/extension_host/src/extension_host.rs
