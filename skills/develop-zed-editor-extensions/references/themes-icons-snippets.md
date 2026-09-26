# Themes, icon themes, and snippets

Cards for the declarative features, which need no Rust. Fixtures:
[`ember-theme/`][ember], [`mono-icons/`][mono], and the Makefile
fixture's [`snippets/makefile.json`][snippets]. `check_theme.py`
validated both JSON files against the published schemas
`themes/v0.2.0.json` and `icon_themes/v0.3.0.json`, fetched on
2026-09-25 (Executed). Host behavior: Zed v1.21.0 source.

## Contents

- [Theme family file](#theme-family-file)
- [Syntax styles](#syntax-styles)
- [Theme colors](#theme-colors)
- [Icon theme file](#icon-theme-file)
- [Icon lookup and fallback](#icon-lookup-and-fallback)
- [Snippets](#snippets)

## Theme family file

**Definition.** A JSON file in `themes/`, discovered automatically. The
top-level object needs `name`, `author`, and `themes`; each theme needs
`name`, `appearance` (`"light"` or `"dark"`), and `style`
([schema][theme-schema], [themes docs][theme-docs]). Zed parses it with
`serde_json_lenient`, so comments are accepted
([theme_settings.rs][theme-settings]). The registry packager rejects a
theme that uses `scrollbar_thumb.background` ([CLI][cli-rs]). A theme
extension may contain only themes ([CLI][cli-rs],
[prerequisites][prereq]).

**Use when.**

- Shipping one family with light and dark variants in one file.

**Do not use when.**

- Adding themes to a language or LSP extension. The packager fails with
  "extension must not provide other features along with themes".
- Taking keys from prose lists unchecked. The themes docs list
  `foreground` as a style property, but neither the v0.2.0 schema nor
  v1.21.0's theme settings source has a top-level `foreground` key. Use
  `text` and `editor.foreground`.

**Example.** Runnable: `assets/examples/ember-theme/themes/ember.json`
(excerpt).

```json
{
  "$schema": "https://zed.dev/schema/themes/v0.2.0.json",
  "name": "Ember",
  "author": "Example Maintainer",
  "themes": [
    {
      "name": "Ember Dark",
      "appearance": "dark",
      "style": {
        "background": "#292524",
        "text": "#e7e5e4",
        "editor.background": "#1c1917",
        "editor.foreground": "#e7e5e4",
        "border": "#44403c",
        "players": [
          {
            "cursor": "#f97316",
            "background": "#f97316",
            "selection": "#f973163d"
          }
        ]
      }
    }
  ]
}
```

**Cost removed.** Schema errors found in Zed instead of before it. The
published schema does not set `additionalProperties: false`, so a
misspelled style key passes validation and is silently unused;
`check_theme.py` prints a `WARN` line for each key the schema does not
list. A warning can also mean "newer than the schema": Zed v1.21.0
reads 48 color keys the v0.2.0 schema lacks, such as
`version_control.added` and `minimap.thumb.background`. That count
compares the `rename` attributes of `ThemeColorsContent` and
`StatusColorsContent` in [theme.rs at v1.21.0][theme-rs] with the
schema's properties, excluding the deprecated
`scrollbar_thumb.background`.

**Verify.**

1. `python3 scripts/check_theme.py themes/ember.json --schema
   themes-v0.2.0.json` prints `0 errors, 0 warnings`. Executed.
1. In Zed, `theme selector: toggle` lists "Ember Dark" and "Ember
   Light" (Not runnable here).

## Syntax styles

**Definition.** `style.syntax` maps a highlight capture name without the
`@` (such as `comment` or `function.builtin`) to
`{ color, background_color, font_style, font_weight }`. `font_style` is
`normal`, `italic`, or `oblique`; `font_weight` is 100–900 in steps of
100 ([schema][theme-schema]).

**Use when.**

- Every capture the languages you care about emit. The Makefile fixture
  emits `comment`, `function`, `function.builtin`, `variable`,
  `variable.special`, `string`, `operator`, `punctuation.bracket`,
  `punctuation.delimiter`, and `keyword`.

**Do not use when.**

- Writing `"@comment"` with the at sign. The key never matches a
  capture.
- Giving `font_weight` as a string such as `"bold"`. The schema enum
  accepts only the integers.

**Example.**

```json
"syntax": {
  "comment": { "color": "#a8a29e", "font_style": "italic" },
  "keyword": { "color": "#f97316", "font_weight": 700 },
  "function": { "color": "#e0823d" },
  "function.builtin": { "color": "#d4a72c" }
}
```

**Cost removed.** Unstyled captures. A capture missing from `syntax`
falls back to a less specific key or gets no color; compare the captures
in your `highlights.scm` with the keys of `syntax`.

**Verify.**

1. `check_theme.py` reports no enum errors. Executed.
1. In Zed, comments in `samples/Makefile` render in italics (Not
   runnable here).

## Theme colors

**Definition.** Colors are hex strings: `#rgb`, `#rgba`, `#rrggbb`, or
`#rrggbbaa`. The parser rejects anything else
("Expected #rgb, #rgba, #rrggbb, or #rrggbbaa") ([gpui color.rs][color-rs]).

**Use when.**

- Every color value in `style`, `players`, `accents`, and `syntax`.
- Alpha forms for overlays such as `search.match_background`
  (`#f9731640`).

**Do not use when.**

- CSS names (`red`), `rgb()`, or `hsl()`. The schema types colors only
  as `string`, so it lets them through.

**Example.** The verify mutant replaces `"#e5484d"` with `"crimson"`:

```text
ERROR /themes/0/style/error: bad color 'crimson'
```

**Cost removed.** Values that pass as strings but fail as colors.
`check_theme.py` counts them as errors (unit test
`test_named_colors_are_rejected` and the verify mutant, Executed).

**Verify.**

1. `sh verify.sh` prints `ok   mutant rejected: named color in a
   theme`. Executed.
1. `check_theme.py` on the real file prints `0 errors`. Executed.

## Icon theme file

**Definition.** A JSON file in `icon_themes/` plus the SVG assets it
references, under `icons/`, with paths relative to the
extension root. Each theme needs `name` and `appearance`. Optional keys:
`directory_icons`, `named_directory_icons`, `chevron_icons`,
`file_stems`, `file_suffixes`, and `file_icons` ([schema][icon-schema],
[icon theme docs][icon-docs]). An icon theme extension may contain
nothing else ([CLI][cli-rs]).

**Use when.**

- Replacing project panel icons for folders and file types.

**Do not use when.**

- Leaving `// ...` comments in the file. The docs example has them and
  Zed may accept them, but this repository's JSON validation and
  `check_theme.py` require strict JSON.
- Referencing icons outside `icons/`. The packager copies icon assets
  only from `icons/` ([CLI][cli-rs]).

**Example.** Runnable: `assets/examples/mono-icons/icon_themes/mono-icons.json`
(excerpt).

```json
{
  "$schema": "https://zed.dev/schema/icon_themes/v0.3.0.json",
  "name": "Mono Icons",
  "author": "Example Maintainer",
  "themes": [
    {
      "name": "Mono Icons",
      "appearance": "dark",
      "directory_icons": {
        "collapsed": "./icons/folder.svg",
        "expanded": "./icons/folder-open.svg"
      },
      "file_stems": { "Makefile": "make" },
      "file_suffixes": { "mk": "make", "md": "markdown" },
      "file_icons": {
        "default": { "path": "./icons/file.svg" },
        "make": { "path": "./icons/make.svg" },
        "markdown": { "path": "./icons/markdown.svg" }
      }
    }
  ]
}
```

**Cost removed.** Broken icons. `check_theme.py --root EXT` checks that
each referenced file exists and prints `missing file ...` for each
missing one.

**Verify.**

1. `check_theme.py icon_themes/mono-icons.json --schema
   icon_themes-v0.3.0.json --root .` prints `0 errors, 0 warnings`.
   Executed.
1. In Zed, `icon theme selector: toggle` lists "Mono Icons" (Not
   runnable here).

## Icon lookup and fallback

**Definition.** For each file, Zed tries `file_stems`, then
`file_suffixes`, in this order: the whole file name, every suffix after
a dot, multi-part extensions, then the extension. The matched value is a
key into `file_icons`. A key missing from `file_icons` takes the default
icon theme's entry for that key; if nothing matches, Zed uses
`file_icons.default` ([file_icons.rs][file-icons-rs]).

**Use when.**

- Mapping fixed names (`Makefile`) with `file_stems` and extensions
  (`mk`) with `file_suffixes`.

**Do not use when.**

- A `file_suffixes` value names a key `file_icons` lacks. The file
  silently shows Zed's default icon for that key. `check_theme.py`
  warns: `'markdown' is not a file_icons key; Zed
  falls back to its default icon theme`.

**Example.** From the unit test, with a dangling `md` mapping:

```text
WARN /themes/0/file_suffixes/md: 'markdown' is not a file_icons key;
Zed falls back to its default icon theme
```

**Cost removed.** Mixed icon sets in the project panel. Each dangling
mapping is one `WARN` line.

**Verify.**

1. `python3 scripts/test_check_theme.py` passes
   `test_dangling_suffix_is_a_warning`. Executed.
1. In Zed, `Makefile` and `rules.mk` show `make.svg` (Not runnable
   here).

## Snippets

**Definition.** VS Code–style JSON objects. Each entry has `body`
(required; a string or list of lines), optional `prefix` (defaults to
the entry name), and optional `description`. A file named
`<lowercase language name>.json` applies to that language;
`snippets.json` applies globally ([snippet provider][snippet-rs],
[snippets docs][snippet-docs]). `extension.toml` lists the files in
`snippets` as a string or list, and a root `snippets.json` is found
automatically ([builder source][builder-rs]). The packager parses every
body and fails on invalid snippet syntax ([CLI][cli-rs]).

**Use when.**

- Language-specific boilerplate, such as a phony target in Makefiles.

**Do not use when.**

- A single-language snippet sits in `snippets.json`. The prerequisites
  ask you to scope language snippets to their languages
  ([prerequisites][prereq]).
- The file name is not the lowercase language name: `make.json` never
  applies to the "Makefile" language.

**Example.** Runnable: `assets/examples/makefile/snippets/makefile.json`.

```json
{
  "Phony target": {
    "prefix": "phony",
    "body": [".PHONY: ${1:target}", "${1:target}:", "\t${2:command}$0"],
    "description": "Declare a phony target with one recipe line"
  }
}
```

**Cost removed.** Retyped boilerplate. `check_extension.py` reports each
snippet without a string or list `body` as an error.

**Verify.**

1. `check_extension.py` prints `0 errors` for the Makefile fixture.
   Executed.
1. In Zed, typing `phony` in a Makefile offers the snippet (Not
   runnable here).

[ember]: ../assets/examples/ember-theme/
[mono]: ../assets/examples/mono-icons/
[snippets]: ../assets/examples/makefile/snippets/makefile.json
[theme-docs]: https://zed.dev/docs/extensions/themes
[icon-docs]: https://zed.dev/docs/extensions/icon-themes
[snippet-docs]: https://zed.dev/docs/extensions/snippets
[prereq]: https://zed.dev/docs/extensions/publishing/prerequisites
[theme-schema]: https://zed.dev/schema/themes/v0.2.0.json
[icon-schema]: https://zed.dev/schema/icon_themes/v0.3.0.json
[theme-settings]: https://github.com/zed-industries/zed/blob/v1.21.0/crates/theme_settings/src/theme_settings.rs
[theme-rs]: https://github.com/zed-industries/zed/blob/v1.21.0/crates/settings_content/src/theme.rs
[color-rs]: https://github.com/zed-industries/zed/blob/v1.21.0/crates/gpui/src/color.rs
[file-icons-rs]: https://github.com/zed-industries/zed/blob/v1.21.0/crates/file_icons/src/file_icons.rs
[snippet-rs]: https://github.com/zed-industries/zed/blob/v1.21.0/crates/snippet_provider/src/lib.rs
[builder-rs]: https://github.com/zed-industries/zed/blob/v1.21.0/crates/extension/src/extension_builder.rs
[cli-rs]: https://github.com/zed-industries/zed/blob/v1.21.0/crates/extension_cli/src/main.rs
