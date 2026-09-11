# Zed language starter

This concrete Bash grammar example pins tree-sitter-bash v0.25.1 by commit.
Replace extension identity, author and repository placeholders. The language
name, suffixes and queries describe Bash, not an arbitrary future language. Zed
already supports shell scripts: do not install or publish a duplicate just to
add server configuration. Use this fixture to validate grammar/query work, or
replace its grammar, language config and queries together for another language.

`outline.scm` captures function names through Bash's `word` node, not an
invented `identifier` node. Highlights cover comments, quoted/raw strings and
variable names. This is a focused query example, not an exhaustive Bash theme.

Compile queries against the pinned parser and check captures on nested
functions, Unicode, strings/comments containing fake declarations, and
incomplete input. Then check representative files through an isolated Dev
Extension; Tree-sitter query success alone does not prove Zed outline or theme
rendering. Run registry validation only when preparing an actual registry
submission.
